from django.db import models
from ckeditor.fields import RichTextField
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User
import uuid
from django.utils import timezone






class PastPaper(models.Model):
    year = models.IntegerField(unique=True)

    def __str__(self):
        return str(self.year)
class Subject(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Question(models.Model):
    TEXT = 'text'
    IMAGE = 'image'

    QUESTION_TYPE_CHOICES = [
        (TEXT, 'Text'),
        (IMAGE, 'Image'),
    ]



    question_number = models.IntegerField(null=True)

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    past_paper = models.ForeignKey(PastPaper, on_delete=models.CASCADE, null=True, blank=True)
    question_type = models.CharField(max_length=5, choices=QUESTION_TYPE_CHOICES, default=TEXT)
    
    text = models.TextField(null=True, blank=True)  # For text-based questions
    text1 = RichTextField(null=True, blank=True)
    diagram = models.ImageField(upload_to='diagrams/', null=True, blank=True,)  # For image-based questions
    explanation = models.TextField(blank=True)
    explanation1 = RichTextField(null=True, blank=True)

        # Answer choices
    option_a = models.CharField(max_length=250)
    option_b = models.CharField(max_length=250)
    option_c = models.CharField(max_length=250)
    option_d = models.CharField(max_length=250)

    # Store the correct answer as A, B, C, or D, and map to respective options
    correct_answer = models.CharField(
        max_length=1,
        choices=[
            ('A', 'option_a'),
            ('B', 'option_b'),
            ('C', 'option_c'),
            ('D', 'option_d')
        ],
        default='A'  # Defaulting to 'A' to avoid migration errors
    )


    def __str__(self):
        return f" {self.subject.name, self.question_number} - {self.past_paper.year if self.past_paper else 'Random'}: {self.text[:50]}"



class Tournament(models.Model):
    name = models.CharField(max_length=200)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    prize_to_win = models.IntegerField(null=True, blank=True)
    Level = models.CharField(max_length=40, null=True, blank=True)

    winners = models.ManyToManyField(User, related_name="tournament_wins", blank=True)
    top_five = models.ManyToManyField(User, related_name="tournament_top5", blank=True)

    finalized = models.BooleanField(default=False)  # to avoid re-finalizing

    def __str__(self):
        return self.name

    def top_leaders(self):
        """Return live top 5 players"""
        return self.scores.order_by('-score')[:5]

    def finalize_results(self):
        """Finalize winners + top 5 when tournament is over"""
        if self.finalized:
            return  # already finalized

        if timezone.now() < self.end_date:
            return  # tournament not yet over

        if not self.scores.exists():
            return  # no players

        # Highest score
        highest_score = self.scores.order_by('-score').first().score

        # All winners in case of tie
        winner_users = self.scores.filter(score=highest_score).values_list('user', flat=True)

        # Top 5 players
        top5_users = self.scores.order_by('-score')[:5].values_list('user', flat=True)

        # Save them
        self.winners.set(winner_users)
        self.top_five.set(top5_users)

        self.finalized = True
        self.save()


    








class Tournament_subject(models.Model):
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name="subjects"
    )
    name = models.CharField(max_length=200)
    time_limit = models.IntegerField(default=300)  # time in seconds (default = 5 minutes)

    class Meta:
        unique_together = ('tournament', 'name')  # Science in Tournament A ≠ Science in Tournament B

    def __str__(self):
        return f"{self.name} ({self.tournament.name})"



class SubjectPlay(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.ForeignKey("Tournament_subject", on_delete=models.CASCADE)
    played_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "subject")  # ensures a user can only play once

    def __str__(self):
        return f"{self.user.username} played {self.subject.name}"





class Tournament_question(models.Model):
    subject = models.ForeignKey(Tournament_subject, on_delete=models.CASCADE, related_name='question')

    TEXT = 'text'
    IMAGE = 'image'

    QUESTION_TYPE_CHOICES = [
        (TEXT, 'Text'),
        (IMAGE, 'Image'),
    ]



    question_number = models.IntegerField(null=True)
    question_type = models.CharField(max_length=5, choices=QUESTION_TYPE_CHOICES, default=TEXT)
    
    text = RichTextField(null=True, blank=True)
    diagram = models.ImageField(upload_to='diagrams/', null=True, blank=True,)  # For image-based questions

        # Answer choices
    option_a = models.CharField(max_length=250)
    option_b = models.CharField(max_length=250)
    option_c = models.CharField(max_length=250)
    option_d = models.CharField(max_length=250)

    # Store the correct answer as A, B, C, or D, and map to respective options
    correct_answer = models.CharField(
        max_length=1,
        choices=[
            ('A', 'option_a'),
            ('B', 'option_b'),
            ('C', 'option_c'),
            ('D', 'option_d')
        ],
        default='A'  # Defaulting to 'A' to avoid migration errors
    )


    def __str__(self):
        return f" {self.subject.name, self.question_number}"







class Score(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name="scores"
    )
    score = models.IntegerField(default=0)

    class Meta:
        unique_together = ('user', 'tournament')

    def __str__(self):
        return f"{self.user.username} - {self.tournament.name}: {self.score}"


class TournamentEnrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="enrollments")
    tournament = models.ForeignKey("Tournament", on_delete=models.CASCADE, related_name="enrollments")
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "tournament")  # prevent duplicate enrollments

    def __str__(self):
        return f"{self.user.username} enrolled in {self.tournament.name}"





class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.IntegerField(null=True)
    school_name = models.CharField(max_length=50, null=True)

    # Each user gets a unique referral code
    referral_code = models.CharField(max_length=10, unique=True, blank=True)

    # Who referred this user (nullable, because some may not be referred)
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="referrals"
    )

    # Number of people they have invited
    invited_count = models.IntegerField(default=0)

    # Whether this user is eligible for lifetime access (or tournament entry)
    lifetime_access = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Generate referral code only once
        if not self.referral_code:
            self.referral_code = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} Profile"
