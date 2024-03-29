from django.shortcuts import render, redirect
from django.http import JsonResponse
from openai import OpenAI
from django.contrib import auth
from django.contrib.auth.models import User
from .models import AssessmentQuestion, AssessmentHistory
from django.shortcuts import render
from django.http import JsonResponse
import os
from dotenv import load_dotenv
import json

from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, user_logged_in
from django_chatbot import settings
from django.core.mail import send_mail,EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth import authenticate, login, logout
from . tokens import generate_token
from django.utils.encoding import force_bytes
try:
    from django.utils.encoding import force_text
except ImportError:
    from django.utils.encoding import force_str as force_text

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI()

def ask_openai(message):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a conversational chatbot."},
            {"role": "user", "content": message},
        ]
    )

    answer = response.choices[0].message.content.strip()
    return answer

# Create your views here.
def chatbot(request):
    if request.method == 'POST':
        message = request.POST.get('message')
        response = ask_openai(message)

        return JsonResponse({'message': message, 'response': response})
    return render(request, 'chatbot.html')

def chat(request):
    if request.method == 'POST':
        message = request.POST.get('message')
        response = ask_openai(message)

        return JsonResponse({'message': message, 'response': response})
    return render(request, 'chat.html')

def signin(request):
    if request.method == 'POST':
        username = request.POST['username']
        pass1 = request.POST['pass1']
        
        user = authenticate(username=username, password=pass1)
        
        if user is not None:
            login(request,user)
            fname = user.first_name
            return render(request, 'chatbot.html', {'fname': fname})
        
        else:
            messages.error(request,"Bad Credentials!")
            return redirect('chatbot')
            
    return render(request, "signin.html")


def register(request):
    if request.method == "POST":
        username = request.POST['username']
        fname = request.POST['fname']
        lname = request.POST['lname']
        email = request.POST['email']
        pass1 = request.POST['pass1']
        pass2 = request.POST['pass2']
        
        if User.objects.filter(username=username):
            messages.error(request, "Username already exist! Please try some other username.")
            return redirect('chatbot')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email Already Registered!!")
            return redirect('chatbot')
        
        if len(username)>20:
            messages.error(request, "Username must be under 20 charcters!!")
            return redirect('chatbot')
        
        if pass1 != pass2:
            messages.error(request, "Passwords didn't matched!!")
            return redirect('chatbot')
        
        if not username.isalnum():
            messages.error(request, "Username must be Alpha-Numeric!!")
            return redirect('chatbot')
        
        myuser = User.objects.create_user(username, email, pass1)
        myuser.first_name = fname
        myuser.last_name = lname
        myuser.is_active = False
        myuser.save()
        messages.success(request, "Your Account has been created succesfully!! Please check your email to confirm your email address in order to activate your account.")
        
        # Welcome Email
        subject = "Welcome to SGPT Login!!"
        message = "Hello " + myuser.first_name + "!! \n" + "Welcome to SGPT!! \nThank you for visiting our website\n. We have also sent you a confirmation email, please confirm your email address. \n\nThanking You"        
        from_email = settings.EMAIL_HOST_USER
        to_list = [myuser.email]
        send_mail(subject, message, from_email, to_list, fail_silently=True)
        
         # Email Address Confirmation Email
        current_site = get_current_site(request)
        email_subject = "Confirm your Email @ SGPT Login!!"
        message2 = render_to_string('email_confirmation.html',{
            
            'name': myuser.first_name,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(myuser.pk)),
            'token': generate_token.make_token(myuser)
        })
        email = EmailMessage(
        email_subject,
        message2,
        settings.EMAIL_HOST_USER,
        [myuser.email],
        )
        email.fail_silently = True
        email.send()
        
        return redirect('signin')
    return render(request, 'register.html')



def logout(request):
    auth.logout(request)
    messages.success(request, "Logged Out Successfully!!")
    return redirect('signin')

def activate(request,uidb64,token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        myuser = User.objects.get(pk=uid)
    except (TypeError,ValueError,OverflowError,User.DoesNotExist):
        myuser = None

    if myuser is not None and generate_token.check_token(myuser,token):
        myuser.is_active = True
        #user.profile.signup_confirmation = True
        myuser.save()
        login(request,myuser)
        messages.success(request, "Your Account has been activated!!")
        return redirect('signin')
    else:
        return render(request,'activation_failed.html')

def activation_failed(request):
    return render(request,'activation_failed.html')


def home(request):
    return render(request,'home.html')

def generate_assessment(message):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a question generator bot that can generate questions of different types. Output should be in a JSON format. also make sure when you generate any type of assessment other than one line questions there must a correct answer generated along with them named answer."},
            {"role": "user", "content": message},
        ]
    )

    answer = response.choices[0].message.content.strip()
    return answer

def assessment(request):
    if not request.user.is_authenticated:
        # Redirect the user to the login page, or return a suitable response
        return redirect('signin') 
    if request.method == 'POST':
        message = request.POST.get('message')
        response = generate_assessment(message)

        # Print the response data for debugging
        print(response)

        # Parse the JSON response
        response_data = json.loads(response)

        # Clear existing AssessmentQuestion objects
        AssessmentQuestion.objects.all().delete()

        # Check if the response contains the "questions" key
        questions_data = response_data.get("questions", [])

        # Create AssessmentQuestion objects for each question
        for question_data in questions_data:
            question = question_data["question"]
            options = question_data.get("options", [])  # Use get() to handle missing keys gracefully
            answer = question_data.get("answer", "")  # Use get() to handle missing keys gracefully

            # Create and save the AssessmentQuestion object
            assessment_question = AssessmentQuestion.objects.create(
                question=question,
                options=options,
                answer=answer,
            )
            assessment_question.save()

        return JsonResponse({'message': message, 'response': response})
    return render(request, 'assessment.html')


def interface(request):
    # Fetch the first 5 questions for display
    assessment_questions = AssessmentQuestion.objects.all()[:5]

    if request.method == 'POST':
        score = 0
        incorrect_answers = {}
        user_answers = []
        for question in assessment_questions:
            selected_options_key = 'selected_options_' + str(question.id)
            submitted_answer = request.POST.getlist(selected_options_key)
            correct_answer = question.answer

            # Check if any selected option matches the correct answer
            if any(option == correct_answer for option in submitted_answer):
                score += 1
            else:
                # Store incorrect answers
                incorrect_answers[question.question] = {
                    'submitted_answer': submitted_answer,
                    'correct_answer': correct_answer,
                }
            
            question_data = {
                'question': question.question,
                'correct_answer': correct_answer,
                'user_answer': submitted_answer[0] if submitted_answer else "No answer"
            }
            user_answers.append(question_data)
                
            assessment_id = f"user_{request.user.id}_assessment_{AssessmentHistory.objects.count() + 1}"
                
            assessment_history = AssessmentHistory.objects.create(
            assessment_id=assessment_id,
            user=request.user,
            score=score,
            result_details=json.dumps(user_answers)  # Convert to JSON string
        )


        return render(request, 'score.html', {'score': score, 'incorrect_answers': incorrect_answers})

    return render(request, 'interface.html', {'assessment_questions': assessment_questions})


def one_line_interface(request):
    # Fetch the first 5 one-line questions for display
    one_line_questions = AssessmentQuestion.objects.all()[:5]  # Assuming OneLineQuestion is your model for one-line questions

    if request.method == 'POST':
        score = 0
        submitted_answers = []
        for question in one_line_questions:
            answer_key = f'answer_{question.id}'
            submitted_answer = request.POST.get(answer_key)
            submitted_answers.append(submitted_answer)
            correct_answer = question.answer
            if submitted_answer == correct_answer:
                score += 1
        
        # Render the score template with the score
        return render(request, 'score.html', {'score': score})

    return render(request, 'one_line_interface.html', {'one_line_questions': one_line_questions})


def true_n_false_interface(request):
    # Fetch the True or False questions for display
    true_false_questions = AssessmentQuestion.objects.all()[:5]  # Assuming TrueFalseQuestion is your model for True or False questions

    if request.method == 'POST':
        score = 0
        incorrect_answers = {}
        submitted_answers = []
        for question in true_false_questions:
            answer_key = f'answer_{question.id}'
            submitted_answer = request.POST.get(answer_key)
            submitted_answers.append(submitted_answer)
            correct_answer = question.answer.lower()  # Convert to lowercase for case-insensitive comparison
            submitted_answer = submitted_answer.lower()# Convert to lowercase for case-insensitive comparison
            if submitted_answer== correct_answer:
                score += 1
            else:
                # Store incorrect answers along with correct options
                incorrect_answers[question.question] = {
                    'submitted_answer': submitted_answer,
                    'correct_answer': correct_answer,
                }
        
        # Render the score template with the score
        return render(request, 'score.html', {'score': score,'incorrect_answers': incorrect_answers})

    return render(request, 'true_n_false_interface.html', {'true_false_questions': true_false_questions})


def assessment_history(request):
    if not request.user.is_authenticated:
        # Redirect the user to the login page, or return a suitable response
        return redirect('signin') 
    # Fetch all assessment history records for the current user
    user_assessment_history = AssessmentHistory.objects.filter(user=request.user)

    return render(request, 'Assessment_History.html', {'assessment_history': user_assessment_history})
