from django import forms

from django.utils import html

class SubmitButtonWidget(forms.Widget):
    def render(self, name, value, attrs=None):
        return '<div class="container"><input type="submit" name="%s" value="%s"></div>' % (html.escape(name), html.escape(value))


class SubmitButtonField(forms.Field):
    def __init__(self, *args, **kwargs):
        if not kwargs:
            kwargs = {}
        kwargs["widget"] = SubmitButtonWidget

        super(SubmitButtonField, self).__init__(*args, **kwargs)

    def clean(self, value):
        return value
        
        
class WordForm(forms.Form):
    word = forms.CharField(label='word', max_length=20)
    lookup_choices=( ('definition','Find meanings'),('synonym','Find synonyms'),('antonym','Find antonyms'),('entailment','What does the verb entail'),('hypernym','Find hypernyms'),('hyponym','Find hyponyms'),('derivation','Find derivations'),('pholonym','Find part holonyms'),('pmeronym','Find part meronyms'),('sholonym','Find substance holonym'),('smeronym','Find substance meronym'),('example','Find examples'),)
    choices=forms.MultipleChoiceField(choices=lookup_choices)
    groupbysenses=forms.BooleanField(label='Grouping by senses',required=False)
    ssubmit=SubmitButtonField(label="",initial="Submit")
