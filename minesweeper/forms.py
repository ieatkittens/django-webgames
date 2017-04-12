from django import forms


class NewGameForm(forms.Form):

    num_mines = forms.IntegerField(
        widget=forms.TextInput(
            attrs={
                'class': 'form-control'
            }
        ),
        initial=10
    )
