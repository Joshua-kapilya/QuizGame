from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, authenticate, logout
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
from django.shortcuts import get_object_or_404
from .models import User
from django.contrib import messages
from django.db.models import F
from django.urls import reverse
from .forms import UserForm, UserProfileForm

from django.shortcuts import render
from .models import Subject, SubjectPlay, PastPaper, Question, Tournament_subject, Tournament_question, Tournament, Score, UserProfile, TournamentEnrollment

#AN4GKMYBK43VWA28UL27AR3C
def get_explanation(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    return JsonResponse({"explanation": question.explanation1})






def home(request):
    subjects = Subject.objects.all()
    now = timezone.now()

    # Get tournaments that ended within the last 24 hours
    recent_tournaments = Tournament.objects.filter(
        end_date__lte=now,
        end_date__gte=now - timezone.timedelta(days=1)
    )

    tournaments_with_leaders = []
    for tournament in recent_tournaments:
        tournament.finalize_results()

        top_scores = tournament.scores.order_by('-score')[:5]
        if top_scores:
            tournaments_with_leaders.append({
                "tournament": tournament,
                "top_scores": top_scores,
                "winner": top_scores[0],
            })

    context = {
        "subjects": subjects,
        "tournaments_with_leaders": tournaments_with_leaders,
    }
    return render(request, "home.html", context)



def tournament_list(request):
    today = timezone.now()

    # ✅ Show all tournaments that have not ended yet
    active_tournaments = Tournament.objects.filter(end_date__gte=today).order_by("start_date")

    return render(request, "tournament_list.html", {
        "tournaments": active_tournaments
    })





@login_required
def tournament_detail(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)

    # Check if tournament is active (still useful for template display)
    active = tournament.start_date <= timezone.now() <= tournament.end_date

    # Check if user already enrolled
    enrollment = TournamentEnrollment.objects.filter(user=request.user, tournament=tournament).first()
    profile = getattr(request.user, "userprofile", None)
    invited_count = profile.invited_count if profile else 0


    # Handle enrollment (still allowed before tournament starts)
    if request.method == "POST" and not enrollment:
        profile = request.user.userprofile
        if profile.invited_count >= 2:
            TournamentEnrollment.objects.create(user=request.user, tournament=tournament)
            messages.success(request, "🎉 You have successfully enrolled in the tournament!")
            return redirect("tournament_detail", pk=tournament.pk)
        else:
            messages.warning(request, "⚠️ Invite at least 2 people to enroll in the tournament.")

    # Get top 5 leaderboard
    top5 = tournament.scores.all().order_by("-score")[:5]

    # Get full leaderboard
    full_leaderboard = tournament.scores.all().order_by("-score")

    # Find user rank
    user_rank, user_score = None, None
    if request.user.is_authenticated and enrollment:
        try:
            user_score_obj = tournament.scores.get(user=request.user)
            user_score = user_score_obj.score

            # Get rank by counting higher scores
            higher_scores = tournament.scores.filter(score__gt=user_score).count()
            user_rank = higher_scores + 1
        except Score.DoesNotExist:
            pass

    return render(request, "tournament_detail.html", {
        "tournament": tournament,
        "active": active,
        "subjects": tournament.subjects.all(),
        "enrollment": enrollment,
        "top5": top5,
        "full_leaderboard": full_leaderboard,
        "user_rank": user_rank,
        "user_score": user_score,
        "invite_url": reverse("profile_view"),
        "invited_count": invited_count,
  # 👈 for the invite button
    })








def subject_questions(request, subject_id):
    subject = get_object_or_404(Tournament_subject, id=subject_id)
    tournament = subject.tournament  

    if not request.user.is_authenticated:
        messages.warning(request, "You must be logged in to access questions.")
        return redirect("login")

    # Check enrollment
    enrolled = TournamentEnrollment.objects.filter(
        user=request.user, tournament=tournament
    ).exists()
    if not enrolled:
        messages.warning(request, "⚠️ You must enroll in this tournament to access the questions.")
        return redirect("tournament_detail", pk=tournament.id)

    # ✅ Check if user already played this subject
    already_played = SubjectPlay.objects.filter(user=request.user, subject=subject).exists()
    if already_played:
        messages.error(request, "❌ You have already played this subject.")
        return redirect("tournament_detail", pk=tournament.id)

    # Otherwise allow playing
    questions = Tournament_question.objects.filter(subject=subject).order_by("question_number")

    # Record that the user is playing this subject
    SubjectPlay.objects.create(user=request.user, subject=subject)

    return render(request, "subject_questions.html", {
        "subject": subject,
        "questions": questions,
        "time_limit": subject.time_limit  # 👈 pass to template
    })


def select_quiz_mode(request, subject_id):
    subject = Subject.objects.get(id=subject_id)

    # Only past papers that have questions for this subject
    past_papers = PastPaper.objects.filter(
        question__subject=subject
    ).distinct().order_by('-year')  # distinct avoids duplicates, order newest first

    return render(request, 'select_quiz_mode.html', {
        'subject': subject,
        'past_papers': past_papers
    })


def get_questions(request, subject_id):
    past_paper_id = request.GET.get('past_paper_id')  # Get selected past paper (if any)

    if past_paper_id:
        questions = Question.objects.filter(subject_id=subject_id, past_paper_id=past_paper_id).order_by('question_number')
    else:
        questions = Question.objects.filter(subject_id=subject_id).order_by('question_number')

    return render(request, 'questions.html', {'questions': questions})




def check_answer(request):
    if request.method == "POST":
        data = json.loads(request.body)
        question_id = data.get("question_id")
        user_answer = data.get("answer_value")

        try:
            question = Question.objects.get(id=question_id)
            correct_answer = question.correct_answer  # Ensure correct_answer exists in the model

            return JsonResponse({"correct": user_answer == correct_answer})

        except Question.DoesNotExist:
            return JsonResponse({"error": "Question not found"}, status=404)

    return JsonResponse({"error": "Invalid request"}, status=400)






def submit_tournament_quiz(request, subject_id):
    if request.method == "POST":
        data = json.loads(request.body)

        answers = data.get("answers", [])

        subject = get_object_or_404(Tournament_subject, id=subject_id)
        questions = Tournament_question.objects.filter(subject=subject)
        tournament = subject.tournament

        correct_count = 0

        for ans in answers:
            q_id = ans.get("question_id")
            user_answer = ans.get("answer_value")

            try:
                question = questions.get(id=q_id)
                if user_answer == question.correct_answer:
                    correct_count += 1
            except Tournament_question.DoesNotExist:
                continue

        total_questions = questions.count()

        # Apply multiplier rule
        if total_questions < 51:
            final_score = correct_count * 3
        else:
            final_score = correct_count * 2.5

        # ✅ Save/update score in DB
        if request.user.is_authenticated:
            score_obj, created = Score.objects.get_or_create(
                user=request.user,
                tournament=tournament,
                defaults={"score": final_score}
            )
            if not created:
                
                score_obj.score += final_score
                score_obj.save()

        # Render results page
        return render(request, "tournament_results.html", {
            "subject": subject,
            "correct_answers": correct_count,
            "total_questions": total_questions,
            "final_score": final_score,
            "tournament": tournament
        })

    return render(request, "error.html", {"message": "Invalid request"})








from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import UserProfile

def signup(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()   # ✅ NEW email field
        phone = request.POST.get("phone", "").strip()
        school_name = request.POST.get("school_name", "").strip()
        password = request.POST.get("password", "")
        password2 = request.POST.get("password2", "")
        referral_code = request.GET.get("ref", "").strip()

        # 🔹 Required fields
        if not all([username, first_name, last_name, email, password, password2, phone, school_name]):
            messages.error(request, "All fields are required.")
            return render(request, "sign_up.html")

        # 🔹 Password check
        if password != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, "sign_up.html")

        # 🔹 Username uniqueness
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, "sign_up.html")

        # 🔹 Email uniqueness
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, "sign_up.html")

        # 🔹 Phone validation
        if not phone.isdigit():
            messages.error(request, "Phone number must contain only digits.")
            return render(request, "sign_up.html")

        if len(phone) < 9 or len(phone) > 15:
            messages.error(request, "Phone number must be between 9 and 15 digits.")
            return render(request, "sign_up.html")

        # ✅ Create user with email
        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,           # ✅ Add email here
            password=password,
        )

        # ✅ Save phone + school_name in UserProfile
        profile = UserProfile.objects.create(
            user=user,
            phone=phone,
            school_name=school_name
        )

        # 🔹 Handle referral logic
        if referral_code:
            try:
                inviter_profile = UserProfile.objects.get(referral_code=referral_code)
                profile.invited_by = inviter_profile.user
                profile.save()

                inviter_profile.invited_count += 1
                if inviter_profile.invited_count >= 2:
                    inviter_profile.lifetime_access = True
                inviter_profile.save()
            except UserProfile.DoesNotExist:
                messages.error(request, "Invalid referral link")

        messages.success(request, "Account created successfully. Please log in.")
        return redirect("login_view")

    return render(request, "sign_up.html")




def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username").strip()
        password = request.POST.get("password")

        if not username or not password:
            messages.error(request, "Both username and password are required.")
            return render(request, "login.html")

        user = authenticate(request, username=username, password=password)
        if user:
            auth_login(request, user)
            messages.success(request, f"Welcome, {user.first_name}!")
            return redirect("home")  # replace with your dashboard/home page
        else:
            messages.error(request, "Invalid username or password.")
            return render(request, "login.html")

    return render(request, "login.html")


def logout_view(request):
    logout(request)  # logs out the current user
    return redirect('home')  # redirect to home page after logout






@login_required
def profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    profile = request.user.userprofile

    # Build referral link
    referral_link = f"{request.build_absolute_uri('/signup/')}?ref={profile.referral_code}"

    context = {
        "profile": profile,
        "referral_link": referral_link,
    }
    return render(request, "profile.html", context)



@login_required
def tournament_standing(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)

    # Get all scores for this tournament
    scores = Score.objects.filter(tournament=tournament).order_by("-score", "user__username")

    # find current user's rank
    try:
        user_score = scores.get(user=request.user)
    except Score.DoesNotExist:
        user_score = None
        return render(request, "tournament_standing.html", {
            "tournament": tournament,
            "user_score": None,
            "position": None,
            "before": [],
            "after": []
        })

    # Make a list of scores with positions
    ranked_scores = list(scores)
    user_index = ranked_scores.index(user_score)
    position = user_index + 1  # 1-based ranking

    # Get two before and two after
    before = ranked_scores[max(0, user_index-2):user_index]
    after = ranked_scores[user_index+1:user_index+3]

    return render(request, "tournament_standing.html", {
        "tournament": tournament,
        "user_score": user_score,
        "position": position,
        "before": before,
        "after": after,
    })


@login_required
def update_profile(request):
    user = request.user
    profile = user.userprofile

    if request.method == "POST":
        user_form = UserForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "✅ Your profile has been updated successfully!")
            return redirect("update_profile")
        else:
            messages.error(request, "⚠️ Please correct the errors below.")
    else:
        user_form = UserForm(instance=user)
        profile_form = UserProfileForm(instance=profile)

    return render(request, "update_profile.html", {
        "user_form": user_form,
        "profile_form": profile_form,
    })
