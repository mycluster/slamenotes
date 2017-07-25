"""slamnotes Models Configuration

Several class-based models. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/db/models/
"""
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.mail import send_mail
from django.core.signing import TimestampSigner
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.forms import ModelForm, Textarea, PasswordInput, EmailInput, ValidationError, HiddenInput
from django.utils import timezone


class UserManager(BaseUserManager):
    """
    A custom user manager class based on UserManager in django.contrib.auth.models
    implementing a user manager that requires an email and a password.
    """
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)

        # Generate a confirmation code based on the user's email and current time.
        signer = TimestampSigner()
        signed_email = signer.sign(user.email)

        # Strip original string and colons
        if not settings.DEBUG:
            user.confirmation_code = signed_email.split(":", 1)[1].replace(':', '')

        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

    def natural_key(self):
        return self.email


def validate_txstate_email(value):
    """Checks that the email input during user creation is a @txstate.edu, returns error if not."""
    if '@txstate.edu' not in value:
        raise ValidationError('Must be a @txstate.edu address')


class User(AbstractBaseUser, PermissionsMixin):
    """
    A custom user class based on AbstractUser implementing a fully featured User model with
    admin-compliant permissions.

    Email and password are required. Other fields are optional.
    """

    email = models.EmailField(
        'email address',
        unique=True,
        error_messages={
            'unique': "A user with that email already exists.",
        },
        validators=[validate_txstate_email]
    )
    first_name = models.CharField('first name', max_length=30, blank=True)
    last_name = models.CharField('last name', max_length=30, blank=True)
    is_staff = models.BooleanField(
        'staff status',
        default=False,
        help_text='Designates whether the user can log into this admin site.',
    )
    is_active = models.BooleanField(
        'active',
        default=True,
        help_text='Designates whether this user should be treated as active. '
                  'Deselect this instead of deleting accounts.',
    )
    date_joined = models.DateTimeField('date joined', default=timezone.now)
    confirmation_code = models.CharField(
        'confirmation code',
        max_length=60,
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
        abstract = False  # Used to output emails in JSON instead of ids

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """Returns the short name for the user."""
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email], **kwargs)


class Channel(models.Model):
    """Channel model"""
    school = models.CharField(max_length=50, default="Texas State University")

    prefix = models.CharField(max_length=4)
    course_number = models.PositiveIntegerField(
        validators=[
            MaxValueValidator(9999),
            MinValueValidator(0)
        ])
    section_number = models.PositiveIntegerField(
        validators=[
            MaxValueValidator(999),
            MinValueValidator(0)
        ])
    postfix = models.CharField(max_length=1, blank=True)

    title = models.CharField(max_length=50)
    instructor = models.CharField(max_length=122)

    first_class_day = models.DateField(default=timezone.now)
    last_class_day = models.DateField(default=timezone.now)

    meeting_day_mon = models.BooleanField(default=False)
    meeting_day_tue = models.BooleanField(default=False)
    meeting_day_wed = models.BooleanField(default=False)
    meeting_day_thu = models.BooleanField(default=False)
    meeting_day_fri = models.BooleanField(default=False)
    meeting_day_sat = models.BooleanField(default=False)

    # Start and end times for class periods, stored in 24-hour time
    start_time_h = models.PositiveIntegerField(
        default=00,
        validators=[
            MaxValueValidator(23),
            MinValueValidator(0)
        ])
    start_time_m = models.PositiveIntegerField(
        default=00,
        validators=[
            MaxValueValidator(59),
            MinValueValidator(0)
        ])

    end_time_h = models.PositiveIntegerField(
        default=00,
        validators=[
            MaxValueValidator(23),
            MinValueValidator(0)
        ])
    end_time_m = models.PositiveIntegerField(
        default=00,
        validators=[
            MaxValueValidator(59),
            MinValueValidator(0)
        ])

    def __str__(self):
        if not self.special:
            return self.number
        return self.special


class Session(models.Model):
    """Class session model"""
    date = models.DateField()

    def __str__(self):
        return self.date


class Note(models.Model):
    """Note model"""
    body_text = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL)
    channel = models.ForeignKey(Channel)
    session = models.ForeignKey(Session, null=True, blank=True)
    created_date = models.DateTimeField('date created', default=timezone.now)
    modified_date = models.DateTimeField('date modified', default=timezone.now)

    def __str__(self):
        return self.body_text


def validate_imgur_url(value):
    """Checks that the url is a valid i.imgur.com, returns error if not."""
    if (not value.startswith('http://i.imgur.com/') and not value.startswith('https://i.imgur.com/')) \
            or (not value.endswith('.png') and not value.endswith('.jpg')):
        raise ValidationError('Must be a valid i.imgur.com url')


class HandwrittenNote(Note):
    """Handwritten Note model"""
    url = models.URLField(validators=[validate_imgur_url])


class NoteForm(ModelForm):
    """Note model form"""
    class Meta:
        model = Note
        fields = ['body_text', 'channel']
        labels = {
            'body_text': '',
        }
        widgets = {
            'body_text': Textarea(attrs={'placeholder': 'Write a note...', 'cols': '', 'rows': ''}),
            'channel': HiddenInput()
        }


class HandwrittenNoteForm(ModelForm):
    """Handwritten note model form"""
    class Meta:
        model = HandwrittenNote
        fields = ['url']
        labels = {
            'url': '',
        }


class SignupForm(ModelForm):
    """User model form"""
    class Meta:
        model = User
        fields = ['email', 'password']

        labels = {
            'email': '',
            'password': '',
        }
        widgets = {
            'email': EmailInput(attrs={'placeholder': 'Email'}),
            'password': PasswordInput(attrs={'placeholder': 'Password'}),
        }


class LoginForm(ModelForm):
    """Login model form"""
    class Meta:
        model = User
        fields = ['email', 'password']

        labels = {
            'email': '',
            'password': '',
        }
        widgets = {
            'email': EmailInput(attrs={'placeholder': 'Email'}),
            'password': PasswordInput(attrs={'placeholder': 'Password'}),
        }


class ChannelForm(ModelForm):
    """Channel model form"""
    class Meta:
        model = Channel
        fields = [
            'title',
            'instructor',
            'prefix',
            'course_number',
            'section_number',
            'postfix',
            'first_class_day',
            'last_class_day',
            'meeting_day_mon',
            'meeting_day_tue',
            'meeting_day_wed',
            'meeting_day_thu',
            'meeting_day_fri',
            'meeting_day_sat',
            'start_time_h',
            'start_time_m',
            'end_time_h',
            'end_time_m',
        ]
        labels = {
            'title': 'Class Title',
            'instructor': 'Instructor',
            'prefix': 'Prefix',
            'course_number': 'Course Number',
            'section_number': 'Section Number',
            'postfix': 'Postfix',
            'first_class_day': 'Class Start Day',
            'last_class_day': 'Last Class Day',
            'meeting_day_mon': 'Monday',
            'meeting_day_tue': 'Tuesday',
            'meeting_day_wed': 'Wednesday',
            'meeting_day_thu': 'Thursday',
            'meeting_day_fri': 'Friday',
            'meeting_day_sat': 'Saturday',
            'start_time_h': 'Start Time (Hour)',
            'start_time_m': 'Start Time (Mins)',
            'end_time_h': 'End Time (Hour)',
            'end_time_m': 'End Time (Mins)',
        }
