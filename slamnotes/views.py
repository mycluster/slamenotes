"""slamnotes Views Configuration

Several function-based views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/views/
"""

from itertools import chain
from operator import attrgetter
from urllib import parse

from django.contrib.auth import authenticate, login
from django.contrib.auth import logout as auth_logout
from django.core.serializers import serialize
from django.http import HttpResponse
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import Note, HandwrittenNote, User, Channel, \
    NoteForm, HandwrittenNoteForm, SignupForm, LoginForm, ChannelForm
from .settings import DEBUG


def index(request):
    """Home page view"""
    account_created = False
    invalid_login = False
    account_not_activated = False
    account_just_activated = False

    if request.method == 'POST':
        form_login = LoginForm(request.POST) if "login-form" in request.POST else LoginForm()
        form_signup = SignupForm(request.POST) if "signup-form" in request.POST else SignupForm()

        if "login-form" in request.POST:
            # Log user in
            email = request.POST.get('email')
            password = request.POST.get('password')
            user = authenticate(email=email, password=password)
            if user is not None:
                if not user.confirmation_code:
                    login(request, user)
                else:
                    # Return an 'account not activated' error message.
                    account_not_activated = True
            else:
                # Return an 'invalid login' error message.
                invalid_login = True

        elif "signup-form" in request.POST and form_signup.is_valid():
            # Create new account
            User.objects.create_user(**form_signup.cleaned_data)
            account_created = True

            if not DEBUG:
                new_user = User.objects.get(email=form_signup.cleaned_data['email'])
                new_user.email_user(
                    'Activate your account',
                    '''Welcome to Slam eNotes!

Visit http://slamenotes.com/activate?%s to activate your account.

Best,
Slam eNotes Team

This message was sent to you because your email was used to register an account at slamenotes.com.'''
                    % new_user.confirmation_code,
                    'account@slamenotes.com'
                )
    else:
        form_login = LoginForm()
        form_signup = SignupForm()
        if request.META['QUERY_STRING'] == 'activated':
            account_just_activated = True

    theme = request.COOKIES.get('theme', '')

    return render(request, 'index.html',
                  {
                      'debug_enabled': DEBUG,
                      'form_login': form_login,
                      'form_signup': form_signup,
                      'account_created': account_created,
                      'invalid_login': invalid_login,
                      'account_not_activated': account_not_activated,
                      'account_just_activated': account_just_activated,
                      'theme': theme,
                  })


def activate(request):
    """Account activation view"""

    if request.META['QUERY_STRING']:
        try:
            user = User.objects.get(confirmation_code=request.META['QUERY_STRING'])
            # Set user's confirmation code to an empty string, signifying the account has been activated.
            user.confirmation_code = ''
            user.save()

            return redirect(reverse('index') + '?activated')
        except User.DoesNotExist:
            pass

    return redirect(index)


def channel(request, pk):
    """Channel view"""
    the_channel = get_object_or_404(Channel, pk=pk)
    notes = Note.objects.order_by('-created_date').filter(channel=pk)
    handwritten_notes = HandwrittenNote.objects.order_by('-created_date')

    all_notes = sorted(chain(notes, handwritten_notes), key=attrgetter('created_date'), reverse=True)

    if request.method == 'POST':
        if request.POST.get('body_text', '') != '':
            note_create(request)
        else:
            channel_create(request)
    
    form = NoteForm({'channel': pk})

    channel_form = ChannelForm()
    channels = Channel.objects.all()

    theme = request.COOKIES.get('theme', '')

    return render(request, 'channel.html',
                  {
                      'debug': DEBUG,
                      'channel': the_channel,
                      'channels': channels,
                      'form': form,
                      'channel_form': channel_form,
                      'notes': all_notes,
                      'user': request.user,
                      'theme': theme,
                  })


def logout(request):
    """Logout view"""
    auth_logout(request)
    return redirect('index')


def ajax(request):
    """Ajax view"""

    if request.GET.get('action', '') == 'delete':
        # Delete note
        deleted = note_delete(request)
        return HttpResponse('Note Deleted' if deleted else 'No changes occurred')

    elif request.GET.get('action', '') == 'load':
        # Load note
        fields = ['body_text', 'created_date']
        if request.user.is_authenticated:
            fields.append('author')

        if 'modified_date' not in request.GET or 'channel' not in request.GET:
            return HttpResponse('{}')

        try:
            the_channel = Channel.objects.get(pk=request.GET['channel'])

            later_than = parse_datetime(parse.unquote(request.GET['modified_date']))
            if later_than is None:
                return HttpResponse('{}')
        except (ValueError, Channel.DoesNotExist):
            return HttpResponse('{}')

        notes = Note.objects.filter(channel=the_channel, modified_date__gte=later_than)
        handwritten_notes = HandwrittenNote.objects.filter(modified_date__gte=later_than)

        all_notes = sorted(chain(notes, handwritten_notes), key=attrgetter('created_date'))

        data = serialize('json', all_notes, fields=fields,
                         use_natural_foreign_keys=True)
        return HttpResponse(data, content_type="application/json; charset=utf-8")

    elif request.GET.get('action', '') == 'edit':
        # Edit note
        edit = note_edit(request)
        return HttpResponse('Note Edited' if edit else 'No changes occurred')

    elif request.method == 'POST':
        # Create note
        created = note_create(request)
        return HttpResponse('Note created' if created else 'No changes occurred')

    return HttpResponse('No changes occurred')


def note_create(request):
    """Create a requested note if user is registered."""
    handwritten_note = 'url' in request.POST and request.POST['url'] != ''

    if handwritten_note:
        posted_form = HandwrittenNoteForm(request.POST, request.FILES)
    else:
        posted_form = NoteForm(request.POST, request.FILES)

    if request.user.is_authenticated() and posted_form.is_valid():
        if 'channel' in request.GET:
            the_channel = request.GET['channel']
        else:
            the_channel = posted_form.cleaned_data['channel']
        if handwritten_note:
            url = posted_form.cleaned_data['url']
            HandwrittenNote.objects.create(url=url, channel=the_channel, author=request.user)
        else:
            body_text = posted_form.cleaned_data['body_text']
            Note.objects.create(body_text=body_text, channel=the_channel, author=request.user)
        return True
    return False


def note_edit(request):
    """Edits a requested note if user has sufficient permissions."""
    posted_form = NoteForm(request.POST, request.FILES)
    try:
        note_id = request.GET['note']
    except KeyError:
        return False
    note = get_object_or_404(Note, pk=note_id)
    if note.author == request.user or request.user.is_superuser:
        if request.user.is_authenticated() and posted_form.is_valid():
            note.body_text = posted_form.cleaned_data['body_text']
            note.modified_date = timezone.now()
            note.save()
            return True
    return False


def note_delete(request):
    """Delete a requested note if user has sufficient permissions."""
    try:
        note_id = request.GET['note']
    except KeyError:
        return False
    note = get_object_or_404(Note, pk=note_id)
    if note.author == request.user or request.user.is_superuser:
        note.body_text = ""
        note.modified_date = timezone.now()
        note.save()
        return True
    return False


def channel_create(request):
    """Create a requested channel if user is registered."""

    posted_form = ChannelForm(request.POST, request.FILES)
    if request.user.is_authenticated() and posted_form.is_valid():
        posted_form.save()
        return True
    return False
