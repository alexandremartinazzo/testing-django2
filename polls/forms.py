from django import forms


class QuestionAdminForm(forms.Form):
    ''' a dummy form with extra unimportant fields for the site admin '''

    question_text = forms.CharField(
        label='The text',
        disabled=True,
    )
    pub_date = forms.DateTimeField(
        label='When should it be published?',
        disabled=True,
    )

    # these are the extra fields
    document = forms.FileField(
        help_text="Upload here something that I won't save",
        widget=forms.ClearableFileInput,
    )
    options = forms.MultipleChoiceField(
        help_text='Select it! I am not looking :-)',
        widget=forms.CheckboxSelectMultiple,
        choices=[(i, i) for i in 'ABCDE'],
    )
