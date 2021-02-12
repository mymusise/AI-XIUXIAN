from transformers import TextGenerationPipeline as OldTextGenerationPipeline
from transformers import TFGPT2LMHeadModel
from transformers import XLNetTokenizer
import tensorflow as tf
from transformers.generation_tf_utils import _create_next_token_logits_penalties
from transformers.generation_tf_utils import calc_banned_ngram_tokens
from transformers.generation_tf_utils import set_tensor_by_indices_to_value
from transformers.generation_tf_utils import calc_banned_bad_words_ids
from transformers.generation_tf_utils import set_tensor_by_indices_to_value
from transformers.generation_tf_utils import tf_top_k_top_p_filtering
from transformers.generation_tf_utils import shape_list
from .tokens import extra_token
import os

model_path =  os.environ.get('MODEL_PATH'):
if model_path is None:
    model_path = '/data2/novels/finetune/models/'
tokenizer = None
if tokenizer is None:
    tokenizer = XLNetTokenizer.from_pretrained(
        model_path, additional_special_tokens=extra_token)


eos_tokens = ["....", ".", "。", "!", "?", "！", "？", "”", "；", "\""]

class TFGPT2LMHeadModel(TFGPT2LMHeadModel):
    # eos_token_ids = {
    #     tokenizer.get_vocab().get("。", 0): 2,
    #     tokenizer.get_vocab().get("”", 0): 1,
    # }
    eos_token_ids = [v for k, v in tokenizer.get_vocab().items() for t in eos_tokens if t in k ]
    eos_token_ids_count = 2
    MIN_LENGTH = 36

    def set_sentence_num(self, num):
        self.eos_token_ids_count = num
    
    def get_min_length(self, length):
        self.MIN_LENGTH = length

    def _generate_no_beam_search(
        self,
        input_ids,
        cur_len,
        max_length,
        min_length,
        do_sample,
        temperature,
        top_k,
        top_p,
        repetition_penalty,
        no_repeat_ngram_size,
        bad_words_ids,
        pad_token_id,
        eos_token_id,
        batch_size,
        vocab_size,
        encoder_outputs,
        attention_mask,
        use_cache,
    ):
        """
        Generate sequences for each example without beam search (num_beams == 1). All returned sequence are generated
        independantly.
        """
        # eos_token_ids = dict(self.eos_token_ids)
        eos_token_ids_count = int(self.eos_token_ids_count)
        # length of generated sentences / unfinished sentences
        unfinished_sents = tf.ones_like(input_ids[:, 0])
        sent_lengths = tf.ones_like(input_ids[:, 0]) * max_length
        add_length = 0

        past = encoder_outputs  # defined for encoder-decoder models, None for decoder-only models

        while cur_len < max_length:
            model_inputs = self.prepare_inputs_for_generation(
                input_ids, past=past, attention_mask=attention_mask, use_cache=use_cache
            )
            outputs = self(**model_inputs)
            next_token_logits = outputs[0][:, -1, :]

            # if model has past, then set the past variable to speed up decoding
            if self._use_cache(outputs, use_cache):
                past = outputs[1]

            # repetition penalty from CTRL paper (https://arxiv.org/abs/1909.05858)
            if repetition_penalty != 1.0:
                next_token_logits_penalties = _create_next_token_logits_penalties(
                    input_ids, next_token_logits, repetition_penalty
                )
                # if next_token_logits.dtype == tf.float16:
                #     next_token_logits_penalties = tf.cast(next_token_logits_penalties, tf.float16)

                next_token_logits = tf.math.multiply(
                    next_token_logits, next_token_logits_penalties)

            if no_repeat_ngram_size > 0:
                # calculate a list of banned tokens to prevent repetitively generating the same ngrams
                # from fairseq: https://github.com/pytorch/fairseq/blob/a07cb6f40480928c9e0548b737aadd36ee66ac76/fairseq/sequence_generator.py#L345
                banned_tokens = calc_banned_ngram_tokens(
                    input_ids, batch_size, no_repeat_ngram_size, cur_len)
                # create banned_tokens boolean mask
                banned_tokens_indices_mask = []
                for banned_tokens_slice in banned_tokens:
                    banned_tokens_indices_mask.append(
                        [True if token in banned_tokens_slice else False for token in range(
                            vocab_size)]
                    )

                next_token_logits = set_tensor_by_indices_to_value(
                    next_token_logits, tf.convert_to_tensor(
                        banned_tokens_indices_mask, dtype=tf.bool), -float("inf")
                )

            if bad_words_ids is not None:
                # calculate a list of banned tokens according to bad words
                banned_tokens = calc_banned_bad_words_ids(
                    input_ids, bad_words_ids)

                banned_tokens_indices_mask = []
                for banned_tokens_slice in banned_tokens:
                    banned_tokens_indices_mask.append(
                        [True if token in banned_tokens_slice else False for token in range(
                            vocab_size)]
                    )

                next_token_logits = set_tensor_by_indices_to_value(
                    next_token_logits, tf.convert_to_tensor(
                        banned_tokens_indices_mask, dtype=tf.bool), -float("inf")
                )

            # set eos token prob to zero if min_length is not reached
            if eos_token_id is not None and cur_len < min_length:
                # create eos_token_id boolean mask
                is_token_logit_eos_token = tf.convert_to_tensor(
                    [True if token is eos_token_id else False for token in range(vocab_size)], dtype=tf.bool
                )
                eos_token_indices_mask = tf.broadcast_to(
                    is_token_logit_eos_token, [batch_size, vocab_size])

                next_token_logits = set_tensor_by_indices_to_value(
                    next_token_logits, eos_token_indices_mask, -float("inf")
                )

            if do_sample:
                # Temperature (higher temperature => more likely to sample low probability tokens)
                if temperature != 1.0:
                    next_token_logits = next_token_logits / temperature
                # Top-p/top-k filtering
                next_token_logits = tf_top_k_top_p_filtering(
                    next_token_logits, top_k=top_k, top_p=top_p)
                # Sample
                next_token = tf.squeeze(
                    tf.random.categorical(next_token_logits, dtype=tf.int32, num_samples=1), axis=1
                )
            else:
                # Greedy decoding
                next_token = tf.math.argmax(
                    next_token_logits, axis=-1, output_type=tf.int32)

            # update generations and finished sentences
            if eos_token_id is not None:
                # pad finished sentences if eos_token_id exist
                tokens_to_add = next_token * unfinished_sents + \
                    (pad_token_id) * (1 - unfinished_sents)
            else:
                tokens_to_add = next_token

            # add token and increase length by one
            input_ids = tf.concat(
                [input_ids, tf.expand_dims(tokens_to_add, -1)], 1)
            cur_len = cur_len + 1
            add_length += 1

            if eos_token_id is not None:
                eos_in_sents = tokens_to_add == eos_token_id
                # if sentence is unfinished and the token to add is eos, sent_lengths is filled with current length
                is_sents_unfinished_and_token_to_add_is_eos = tf.math.multiply(
                    unfinished_sents, tf.cast(eos_in_sents, tf.int32)
                )
                sent_lengths = (
                    sent_lengths *
                    (1 - is_sents_unfinished_and_token_to_add_is_eos)
                    + cur_len * is_sents_unfinished_and_token_to_add_is_eos
                )

                # unfinished_sents is set to zero if eos in sentence
                unfinished_sents -= is_sents_unfinished_and_token_to_add_is_eos

            # stop when there is a </s> in each sentence, or if we exceed the maximul length
            if tf.math.reduce_max(unfinished_sents) == 0:
                break

            id_to_add = tokens_to_add.numpy()[0]
            if id_to_add in self.eos_token_ids:
                eos_token_ids_count -= 1
                if eos_token_ids_count <= 0 and add_length >= self.MIN_LENGTH:
                    break

            # extend attention_mask for new generated input if only decoder
            if self.config.is_encoder_decoder is False:
                attention_mask = tf.concat(
                    [attention_mask, tf.ones((shape_list(attention_mask)[0], 1), dtype=tf.int32)], axis=-1
                )

        # if there are different sentences lengths in the batch, some batches have to be padded
        min_sent_length = tf.math.reduce_min(sent_lengths)
        max_sent_length = tf.math.reduce_max(sent_lengths)
        if min_sent_length != max_sent_length:
            assert pad_token_id is not None, "`Pad_token_id` has to be defined if batches have different lengths"
            # finished sents are filled with pad_token
            padding = tf.ones(
                [batch_size, max_sent_length.numpy()], dtype=tf.int32) * pad_token_id

            # create length masks for tf.where operation
            broad_casted_sent_lengths = tf.broadcast_to(
                tf.expand_dims(sent_lengths, -1), [batch_size, max_sent_length]
            )
            broad_casted_range = tf.transpose(
                tf.broadcast_to(tf.expand_dims(
                    tf.range(max_sent_length), -1), [max_sent_length, batch_size])
            )

            decoded = tf.where(broad_casted_range <
                               broad_casted_sent_lengths, input_ids, padding)
        else:
            decoded = input_ids
        return decoded


class TextGenerationPipeline(OldTextGenerationPipeline):

    def __call__(
        self,
        text_inputs,
        return_tensors=False,
        return_text=True,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False,
        prefix=None,
        **generate_kwargs
    ):
        """
        Complete the prompt(s) given as inputs.

        Args:
            args (:obj:`str` or :obj:`List[str]`):
                One or several prompts (or one list of prompts) to complete.
            return_tensors (:obj:`bool`, `optional`, defaults to :obj:`False`):
                Whether or not to include the tensors of predictions (as token indices) in the outputs.
            return_text (:obj:`bool`, `optional`, defaults to :obj:`True`):
                Whether or not to include the decoded texts in the outputs.
            clean_up_tokenization_spaces (:obj:`bool`, `optional`, defaults to :obj:`False`):
                Whether or not to clean up the potential extra spaces in the text output.
            prefix (:obj:`str`, `optional`):
                Prefix added to prompt.
            generate_kwargs:
                Additional keyword arguments to pass along to the generate method of the model (see the generate method
                corresponding to your framework `here <./model.html#generative-models>`__).

        Return:
            A list or a list of list of :obj:`dict`: Each result comes as a dictionary with the following keys:

            - **generated_text** (:obj:`str`, present when ``return_text=True``) -- The generated text.
            - **generated_token_ids** (:obj:`torch.Tensor` or :obj:`tf.Tensor`, present when ``return_tensors=True``)
              -- The token ids of the generated text.
        """

        if isinstance(text_inputs, str):
            text_inputs = [text_inputs]
        results = []
        for prompt_text in text_inputs:
            # Manage correct placement of the tensors
            with self.device_placement():
                prefix = prefix if prefix is not None else self.model.config.prefix
                if prefix is None and self.model.__class__.__name__ in [
                    "XLNetLMHeadModel",
                    "TransfoXLLMHeadModel",
                    "TFXLNetLMHeadModel",
                    "TFTransfoXLLMHeadModel",
                ]:
                    # For XLNet and TransformerXL we add an article to the prompt to give more state to the model.
                    prefix = self.XL_PREFIX

                if prefix:
                    prefix_inputs = self._parse_and_tokenize(
                        prefix, padding=False, add_special_tokens=False)
                    # This impacts max_length and min_length argument that need adjusting.
                    prefix_length = prefix_inputs["input_ids"].shape[-1]
                    if generate_kwargs.get("max_length", None) is not None:
                        generate_kwargs["max_length"] += prefix_length
                    if generate_kwargs.get("min_length", None) is not None:
                        generate_kwargs["min_length"] += prefix_length

                prefix = prefix or ""
                inputs = self._parse_and_tokenize(
                    prefix + prompt_text, padding=False, add_special_tokens=False)

                # set input_ids to None to allow empty prompt
                if inputs["input_ids"].shape[-1] == 0:
                    inputs["input_ids"] = None
                    inputs["attention_mask"] = None

                if self.framework == "pt" and inputs["input_ids"] is not None:
                    inputs = self.ensure_tensor_on_device(**inputs)

                input_ids = inputs["input_ids"]

                # Ensure that batch size = 1 (batch generation not allowed for now)
                assert (
                    input_ids is None or input_ids.shape[0] == 1
                ), "Batch generation is currently not supported. See https://github.com/huggingface/transformers/issues/3021 for more information."

                output_sequences = self.model.generate(
                    input_ids=input_ids, **generate_kwargs)  # BS x SL

            result = []
            for generated_sequence in output_sequences:
                if self.framework == "pt" and generated_sequence is not None:
                    generated_sequence = generated_sequence.cpu()
                generated_sequence = generated_sequence.numpy().tolist()
                record = {}
                if return_tensors:
                    record["generated_token_ids"] = generated_sequence
                if return_text:
                    # Decode text
                    text = self.tokenizer.decode(
                        generated_sequence,
                        skip_special_tokens=skip_special_tokens,
                        clean_up_tokenization_spaces=clean_up_tokenization_spaces,
                    )

                    # Remove PADDING prompt of the sequence if XLNet or Transfo-XL model is used
                    if input_ids is None:
                        prompt_length = 0
                    else:
                        prompt_length = len(
                            self.tokenizer.decode(
                                input_ids[0],
                                skip_special_tokens=skip_special_tokens,
                                clean_up_tokenization_spaces=clean_up_tokenization_spaces,
                            )
                        )

                    record["generated_text"] = prompt_text + \
                        text[prompt_length:]

                result.append(record)
            results += [result]

        if len(results) == 1:
            return results[0]

        return results
