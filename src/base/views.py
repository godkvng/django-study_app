from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect

from .forms import RoomForm
from .models import Room, Topic, Message


# rooms = [
# 	{'id': 1, 'name': 'Let\'s learn Python'},
# 	{'id': 2, 'name': 'Design with me'},
# 	{'id': 3, 'name': 'Frontend Devs'},
# ]


def login_page(request):
	page = 'login'
	if request.user.is_authenticated:
		return redirect('home')

	if request.method == 'POST':
		username = request.POST.get('username').lower()
		password = request.POST.get('password').lower()
		try:
			user = User.objects.get(username=username)
		except:
			messages.error(request, 'User does not exist')

		user = authenticate(request, username=username, password=password)
		if user is not None:
			login(request, user)
			return redirect('home')
		else:
			messages.error(request, 'Username or password does not exist')
	context = {'page': page}
	return render(request, 'base/login_register.html', context)


def logout_user(request):
	logout(request)
	return redirect('home')


def register_user(request):
	form = UserCreationForm()

	if request.method == 'POST':
		form = UserCreationForm(request.POST)
		if form.is_valid():
			user = form.save(commit=False)
			user.username = user.username.lower()
			user.save()
			login(request, user)
			return redirect('home')
		else:
			messages.error(request, "An error occured during registration")
	context = {
		'form': form,
	}
	return render(request, 'base/login_register.html', context)


def home(request):
	q = request.GET.get('q') if request.GET.get('q') != None else ''
	rooms = Room.objects.filter(
		Q(topic__name__icontains=q) |
		Q(name__icontains=q) |
		Q(description__icontains=q)
	)
	# rooms = Room.objects.all()
	topics = Topic.objects.all()
	room_count = rooms.count()
	comments = Message.objects.all()
	context = {
		'rooms': rooms,
		'topics': topics,
		'room_count': room_count,
		'comments': comments,
	}
	return render(request, 'base/home.html', context)


def room(request, pk):
	# room = None
	# for i in rooms:
	# 	if i['id'] == int(pk):
	# 		room = i
	room = Room.objects.get(id=pk)
	comments = room.message_set.all().order_by('created')
	participants = room.participants.all()

	# Creating message when user writes new message
	if request.method == 'POST':
		message = Message.objects.create(
			user=request.user,
			room=room,
			body=request.POST.get('body')
		)
		room.participants.add(request.user)
		return redirect('room', pk=room.id)

	context = {'room': room, 'comments': comments, 'participants': participants}
	return render(request, 'base/room.html', context)


@login_required(login_url='login')
def create_room(request):
	form = RoomForm()
	if request.method == 'POST':
		form = RoomForm(request.POST)
		if form.is_valid():
			form.save()
			return redirect('home')

	context = {'form': form}
	return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def update_room(request, pk):
	room = Room.objects.get(id=pk)
	form = RoomForm(instance=room)

	if request.user != room.host:
		return HttpResponse('You are not allowed here!')

	if request.method == 'POST':
		form = RoomForm(request.POST, instance=room)
		if form.is_valid():
			form.save()
			return redirect('home')

	context = {'form': form}
	return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def delete_room(request, pk):
	room = Room.objects.get(id=pk)

	if request.user != room.host:
		return HttpResponse('You are not allowed here!')
	if request.method == 'POST':
		room.delete()
		return redirect('home')
	context = {'obj': room}
	return render(request, 'base/delete.html', context)


@login_required(login_url='login')
def delete_message(request, pk):
	message = Message.objects.get(id=pk)

	if request.user != message.user:
		return HttpResponse('You are not allowed here!')
	if request.method == 'POST':
		message.delete()
		return redirect('home')
	context = {'obj': message}
	return render(request, 'base/delete.html', context)
