# Dashboard
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from .forms import WorkoutForm, BootstrapAuthenticationForm, BootstrapUserCreationForm
from django.contrib.auth.decorators import login_required
from .models import Workout, UserProfile
from .forms import WorkoutForm


def home(request):
    # if already logged in, skip landing page and go straight to workouts
    if request.user.is_authenticated:
        return redirect('workout_list')
    return render(request, 'tracker/home.html')


# @login_required means: if you're not logged in, go to the login page
@login_required
def workout_list(request):
    # filter() means: only get workouts belonging to THIS user
    workouts = Workout.objects.filter(user=request.user).order_by('-date')
    return render(request, 'tracker/workout_list.html', {'workouts': workouts})


@login_required
def add_workout(request):
    if request.method == 'POST':
        form = WorkoutForm(request.POST)
        if form.is_valid():
            workout = form.save(commit=False)  # pause before saving
            workout.user = request.user        # attach logged-in user
            workout.save()                     # now save to db
            return redirect('workout_list')
    else:
        form = WorkoutForm()
    return render(request, 'tracker/add_workout.html', {'form': form})


@login_required
def edit_workout(request, pk):
    # pk means "primary key" — the unique ID of the workout
    # get_object_or_404 means: find this workout, or show a 404 error
    workout = get_object_or_404(Workout, pk=pk, user=request.user)
    if request.method == 'POST':
        form = WorkoutForm(request.POST, instance=workout)
        if form.is_valid():
            form.save()
            return redirect('workout_list')
    else:
        form = WorkoutForm(instance=workout)
    return render(request, 'tracker/edit_workout.html', {'form': form, 'workout': workout})


@login_required
def delete_workout(request, pk):
    workout = get_object_or_404(Workout, pk=pk, user=request.user)
    if request.method == 'POST':
        workout.delete()
        return redirect('workout_list')
    return render(request, 'tracker/delete_workout.html', {'workout': workout})



def register_view(request):
    if request.user.is_authenticated:
        return redirect('workout_list')
    if request.method == 'POST':
        form = BootstrapUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('workout_list')
    else:
        form = BootstrapUserCreationForm()
    return render(request, 'tracker/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('workout_list')
    if request.method == 'POST':
        form = BootstrapAuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('workout_list')
    else:
        form = BootstrapAuthenticationForm()
    return render(request, 'tracker/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


# Dashboard Page
@login_required
def dashboard(request):
    today = timezone.now().date()
    
    # start of current week (Monday)
    start_of_week = today - timedelta(days=today.weekday())
    
    # ALL workouts for this user
    all_workouts = Workout.objects.filter(user=request.user)
    
    # total workouts ever logged
    total_workouts = all_workouts.count()
    
    # total minutes ever logged
    total_minutes = all_workouts.aggregate(
        Sum('duration'))['duration__sum'] or 0
    
    # this week's workouts
    this_week = all_workouts.filter(date__gte=start_of_week)
    
    # minutes logged this week
    weekly_minutes = this_week.aggregate(
        Sum('duration'))['duration__sum'] or 0
    
    # most logged activity
    most_logged = all_workouts.values('activity').annotate(
        count=Count('activity')).order_by('-count').first()
    
    # last 7 days for the chart
    last_7_days = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        minutes = all_workouts.filter(date=day).aggregate(
            Sum('duration'))['duration__sum'] or 0
        last_7_days.append({
            'day': day.strftime('%a'),  # Mon, Tue etc
            'minutes': minutes
        })

    context = {
        'total_workouts': total_workouts,
        'total_minutes': total_minutes,
        'weekly_minutes': weekly_minutes,
        'most_logged': most_logged['activity'] if most_logged else 'None yet',
        'last_7_days': last_7_days,
    }
    return render(request, 'tracker/dashboard.html', context)


# Progress Page
@login_required
def progress(request):
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())

    # get or create profile for this user
    profile, created = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={'weekly_goal': 150}
    )

    # handle goal update form submission
    if request.method == 'POST':
        new_goal = request.POST.get('weekly_goal')
        if new_goal and int(new_goal) > 0:
            profile.weekly_goal = int(new_goal)
            profile.save()
        return redirect('progress')

    # weekly minutes so far
    weekly_minutes = Workout.objects.filter(
        user=request.user,
        date__gte=start_of_week
    ).aggregate(Sum('duration'))['duration__sum'] or 0

    # progress percentage toward goal
    goal = profile.weekly_goal
    percentage = min(int((weekly_minutes / goal) * 100), 100) if goal > 0 else 0

    # calculate streak
    streak = 0
    check_date = today
    while True:
        worked_out = Workout.objects.filter(
            user=request.user,
            date=check_date
        ).exists()
        if worked_out:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    # last 4 weeks summary
    weeks = []
    for i in range(3, -1, -1):
        week_start = start_of_week - timedelta(weeks=i)
        week_end = week_start + timedelta(days=6)
        mins = Workout.objects.filter(
            user=request.user,
            date__gte=week_start,
            date__lte=week_end
        ).aggregate(Sum('duration'))['duration__sum'] or 0
        weeks.append({
            'label': f"Week of {week_start.strftime('%b %d')}",
            'minutes': mins,
            'hit_goal': mins >= goal
        })
        
    # calculate mins remaining
    mins_remaining = max(goal - weekly_minutes, 0)

    context = {
        'weekly_minutes': weekly_minutes,
        'weekly_goal': goal,
        'percentage': percentage,
        'streak': streak,
        'weeks': weeks,
        'mins_remaining': mins_remaining,
    }
    return render(request, 'tracker/progress.html', context)