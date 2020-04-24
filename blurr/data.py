# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/01_data.ipynb (unless otherwise specified).

__all__ = ['HF_BaseInput', 'HF_Tokenizer', 'HF_BatchTransform', 'HF_TextBlock']

# Cell
from .utils import *

import torch
from transformers import *
from fastai2.text.all import *

# Cell
class HF_BaseInput(list): pass

# Cell
class HF_Tokenizer():
    def __init__(self, hf_arch, hf_tokenizer, **kwargs):
        self.hf_arch = hf_arch
        self.hf_tokenizer = hf_tokenizer

    def __call__(self, items):
        for txt in items: yield self._tokenize(txt)

    def _tokenize(self, txt):
        return self.hf_tokenizer.tokenize(txt)

# Cell
class HF_BatchTransform(Transform):

    def __init__(self, hf_arch, hf_tokenizer, max_seq_len=512, truncation_strategy='longest_first'):

        self.hf_arch = hf_arch
        self.hf_tokenizer = hf_tokenizer
        store_attr(self, 'max_seq_len, truncation_strategy')

    def encodes(self, samples):

        encoded_samples = []
        for idx, sample in enumerate(samples):

            if (isinstance(sample[0], tuple)):
                a_tok_ids = sample[0][0].tolist()
                b_tok_ids = sample[0][1].tolist()
            else:
                a_tok_ids = sample[0].tolist()
                b_tok_ids = None

            res = self.hf_tokenizer.prepare_for_model(a_tok_ids, b_tok_ids,
                                                      max_length=self.max_seq_len,
                                                      pad_to_max_length=True,
                                                      truncation_strategy=self.truncation_strategy,
                                                      return_tensors='pt')

            input_ids = res['input_ids'][0]
            token_type_ids = res['token_type_ids'][0] if ('token_type_ids' in res) else torch.tensor([-9999])
            attention_mask = res['attention_mask'][0] if ('attention_mask' in res) else torch.tensor([-9999])

            inputs = [input_ids, token_type_ids, attention_mask]
            targets = sample[1:]

            encoded_samples.append((HF_BaseInput(inputs), *targets))

        return encoded_samples

# Cell
class HF_TextBlock(TransformBlock):

    @delegates(Numericalize.__init__)
    def __init__(self, tok_tfms, hf_arch, hf_tokenizer,
                 hf_batch_tfm=None, vocab=None, max_seq_len=512, **kwargs):

        if hf_batch_tfm is None:
            hf_batch_tfm = HF_BatchTransform(hf_arch, hf_tokenizer, max_seq_len=max_seq_len,
                                             truncation_strategy='longest_first')

        return super().__init__(type_tfms=[*tok_tfms, Numericalize(vocab, **kwargs)],
                                dl_type=SortedDL,
                                dls_kwargs={ 'before_batch': hf_batch_tfm })

    @classmethod
    @delegates(Tokenizer.from_df, keep=True)
    def from_df(cls, text_cols_lists, hf_arch, hf_tokenizer,
                res_col_names=None, vocab=None,
                hf_batch_tfm=None, max_seq_len=512, **kwargs):

        # grab hf tokenizer class to do the actual tokenization (via tok_func) and its vocab
        tokenizer_cls = partial(HF_Tokenizer, hf_arch=hf_arch, hf_tokenizer=hf_tokenizer)
        if (vocab is None): vocab = list(hf_tokenizer.get_vocab())

        # build the column name(s) returned after tokenization
        if (res_col_names is None): res_col_names = [ f'text{i}' for i in range(len(text_cols_lists)) ]

        tok_tfms = [ Tokenizer.from_df(text_cols,
                                       res_col_name=res_col_name,
                                       tok_func=tokenizer_cls,
                                       rules=[], **kwargs)
                    for text_cols, res_col_name in zip(text_cols_lists, res_col_names) ]

        return cls(tok_tfms, hf_arch=hf_arch, hf_tokenizer=hf_tokenizer,
                   hf_batch_tfm=hf_batch_tfm, vocab=vocab, max_seq_len=max_seq_len)

# Cell
@typedispatch
def show_batch(x:HF_BaseInput, y, samples, hf_tokenizer, ctxs=None, max_n=6, **kwargs):
    if ctxs is None: ctxs = get_empty_df(min(len(samples), max_n))

    samples = samples = L((TitledStr(hf_tokenizer.decode(inp)),*s[1:]) for inp, s in zip(x[0], samples))
    ctxs = show_batch[object](x, y, samples, max_n=max_n, ctxs=ctxs, **kwargs)

    display_df(pd.DataFrame(ctxs))
    return ctxs