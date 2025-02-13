from django.http import HttpResponse, JsonResponse
from django.http.response import HttpResponseRedirect
from .models import *
from .decorators import *
from .forms import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login , logout
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render,redirect
from django.contrib.auth.models import User
import re
import requests
import json
from django.contrib import messages

#BIGCHAIN DB
from .more_updates import *
from .queries import *
from bigchaindb_driver import BigchainDB
from bigchaindb_driver.crypto import generate_keypair
from time import sleep
from sys import exit

# Create your views here.

@unauthenticated_user
def login(request):
    if request.method == 'POST':
        login_key = request.POST.get('login_key',False)
        if login_key == False:
            return register(request)
        username = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request,username=username,password=password)

        if user is not None:
            auth_login(request,user)
            return redirect('hospital_profile')
        else:
            err = "Email or password is wrong."
            context = {'err':err}
            return render(request,'application/landing/index.html',context)
    return render(request,'application/landing/index.html')
@unauthenticated_user
def register(request):
    form = NewUserForm()
    err = None
    if request.method == 'POST':
        form = NewUserForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            raw_password = form.cleaned_data.get('password1')
            try:
                User.objects.get(username=email)
            except User.DoesNotExist:
                user = User.objects.create_user(username=email,email=email,password = raw_password)
                hospital_key = generate_keypair()
                hospital = Hospital.objects.create(
                        user = user,
                        name = request.POST.get('hospital-name'),
                        country = request.POST.get('country'),
                        city = request.POST.get('city'),
                        street = request.POST.get('street'),
                        number = request.POST.get('number'),
                        public_key = hospital_key.public_key,
                        private_key = hospital_key.private_key
                )
                pfizer_vaccine = Vaccine.objects.get(brand='Pfizer')
                avail_pfizer = AvailabeVaccines.objects.create(
                    hospital = hospital,
                    vaccine = pfizer_vaccine
                )
                moderna_vaccine = Vaccine.objects.get(brand='Moderna')
                avail_pfizer = AvailabeVaccines.objects.create(
                    hospital = hospital,
                    vaccine = moderna_vaccine
                )
                johnson_vaccine = Vaccine.objects.get(brand='Johnson & Johnson')
                avail_pfizer = AvailabeVaccines.objects.create(
                    hospital = hospital,
                    vaccine = johnson_vaccine
                )
                astra_vaccine = Vaccine.objects.get(brand='AstraZeneca')
                avail_pfizer = AvailabeVaccines.objects.create(
                    hospital = hospital,
                    vaccine = astra_vaccine
                )
        
                auth_login(request,user)
                return redirect("hospital_profile")
            err = "E-mail already exist."
            return render(request, 'application/landing/index.html',{'form':form,'err':err})
        else:
            err = form.errors
    
    return render(request, 'application/landing/index.html',{'form':form,'err':err})

@login_required(login_url="login")  
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required(login_url="login")
def hospital_profile(request):
    current_user = request.user
    current_hospital = Hospital.objects.get(user=current_user)
    
    pfizer_vaccine = Vaccine.objects.get(brand='Pfizer')
    current_pfizer = AvailabeVaccines.objects.get(hospital=current_hospital, vaccine = pfizer_vaccine)
    
    moderna_vaccine = Vaccine.objects.get(brand='Moderna')
    current_moderna = AvailabeVaccines.objects.get(hospital=current_hospital, vaccine = moderna_vaccine)
    
    johnson_vaccine = Vaccine.objects.get(brand='Johnson & Johnson')
    current_johnson = AvailabeVaccines.objects.get(hospital=current_hospital, vaccine = johnson_vaccine)
    
    astra_vaccine = Vaccine.objects.get(brand='AstraZeneca')
    current_astra = AvailabeVaccines.objects.get(hospital=current_hospital, vaccine = astra_vaccine)

    if request.method=="POST":
        name = request.POST.get('hospital-name')
        country = request.POST.get('country')
        city = request.POST.get('city')
        street = request.POST.get('street')
        number = request.POST.get('number')
        email = request.POST.get('email')
        
        pfizer_avail_doses = request.POST.get('pfizer-doses')
        moderna_avail_doses = request.POST.get('moderna-doses')
        johnson_avail_doses = request.POST.get('johnson-doses')
        astra_avail_doses = request.POST.get('astra-doses')

        current_user.email = email
        current_hospital.name = name
        current_hospital.country = country
        current_hospital.city = city
        current_hospital.street = street
        current_hospital.number = number
        
        current_pfizer.free_amount = pfizer_avail_doses
        current_moderna.free_amount = moderna_avail_doses
        current_johnson.free_amount = johnson_avail_doses
        current_astra.free_amount = astra_avail_doses

        current_pfizer.save()
        current_moderna.save()
        current_johnson.save()
        current_astra.save()
        
        current_user.save()
        current_hospital.save()

        context = {'current_hospital':current_hospital, 'current_pfizer':current_pfizer,'current_moderna':current_moderna, 'current_johnson':current_johnson, 'current_astra':current_astra}
        return redirect("/profile")

    context = {'current_hospital':current_hospital, 'current_pfizer':current_pfizer,'current_moderna':current_moderna, 'current_johnson':current_johnson, 'current_astra':current_astra}
    return render(request, 'application/authenticated/profile.html',context)

@login_required(login_url="login")
def add_vaccination(request):
    current_user = request.user
    current_hospital = Hospital.objects.get(user=current_user)

    if request.method=="POST":
        ssid = request.POST.get('amka')
        first_name = request.POST.get('fname')
        last_name = request.POST.get('lastname')
        gender = request.POST.get('mySelect')
        age = request.POST.get('age')
        address = request.POST.get('street')
        city = request.POST.get('city')
        country = request.POST.get('country')
        vbrand = request.POST.get('vbrand')
        dose_a = request.POST.get('dosea')
        dose_b = request.POST.get('doseb')
        completed_doses = request.POST.get('compldoses')
        status = request.POST.get('status')
        symptoms = request.POST.get('symptoms')
        if dose_b == "": 
            dose_b = None
        elif dose_b <= dose_a:
            message = "The second dose have to be after the first one."
            context = {'err':message}
            return render(request, 'application/authenticated/add_vaccination.html',context)

        vaccine = Vaccine.objects.get(brand=vbrand)
        avl_doses_of_vacc = AvailabeVaccines.objects.get(hospital=current_hospital,vaccine=vaccine)
    
        if status == 'canceled':
            avl_doses_of_vacc.free_amount += vaccine.doses
            avl_doses_of_vacc.reserved -= vaccine.doses
        else:
            if avl_doses_of_vacc.free_amount >= vaccine.doses:
                avl_doses_of_vacc.free_amount -= vaccine.doses
                avl_doses_of_vacc.reserved += vaccine.doses
                avl_doses_of_vacc.save()
            else:
                message = "Τhere is no available doses for:" + vaccine.brand
                context = {'err':message}
                return render(request, 'application/authenticated/add_vaccination.html',context)
        create_vaccination(
            current_hospital.public_key,
            current_hospital.private_key,
            current_hospital.pk,
            ssid,
            first_name,
            age,
            gender,
            address,
            country,
            city,
            vaccine.brand,
            status,
            completed_doses,
            symptoms,
            dose_a,
            dose_b,
            current_hospital.name
        )
        messages.success(request,"Τhe new vaccination was successfully registered.")
        return HttpResponseRedirect("/addVaccination")

    return render(request, 'application/authenticated/add_vaccination.html')

@login_required(login_url="login")
def update_vaccination(request,amka):
    current_user = request.user
    current_hospital = Hospital.objects.get(user=current_user)
    current_vaccintaion_bigchain_record = search_amka(amka)
    
    #vaccination with this amka not exist
    if len(current_vaccintaion_bigchain_record) == 2:
        return redirect('hospital_profile')
    
    vaccination_json = json.loads(current_vaccintaion_bigchain_record)

    hospital_json = vaccination_json[0]['hospital']
    hospital_json = Hospital.objects.get(name=hospital_json)
    #to nosokomeio poy ekane ton emvoliasmo tautizetai me to noskomeio pou zitaei na kanei update
    if hospital_json != current_hospital:
        return redirect('hospital_profile')

    if request.method == "POST":
        ssid = request.POST.get('amka')
        first_name = request.POST.get('fname')
        last_name = request.POST.get('lastname')
        gender = request.POST.get('mySelect')
        age = request.POST.get('age')
        address = request.POST.get('street')
        city = request.POST.get('city')
        country = request.POST.get('country')
        vbrand = request.POST.get('vbrand')
        dose_a = request.POST.get('dosea')
        dose_b = request.POST.get('doseb')
        completed_doses = request.POST.get('compldoses')
        status = request.POST.get('status')
        symptoms = request.POST.get('symptoms')

        print("SYMPTOMS: " + symptoms)

        print("=============================\n")
        print(ssid,first_name,symptoms)
        print("=============================\n")

       
        if dose_b <= dose_a:
            message = "The second dose have to be after the first one."
            print(message)
            current_vaccintaion_bigchain_record = search_amka(amka)
            vaccination_json = json.loads(current_vaccintaion_bigchain_record)
            context = {
                'current_amka':vaccination_json[0]['amka'],
                'current_name':vaccination_json[0]['name'],
                'current_age':vaccination_json[0]['age'],
                'current_gender':vaccination_json[0]['gender'],
                'current_country':vaccination_json[0]['country'],
                'current_city':vaccination_json[0]['city'],
                'current_address':vaccination_json[0]['address'],
                'current_vaccine_brand':vaccination_json[0]['vaccine_brand'],
                'current_first_dose':vaccination_json[0]['first_dose_date'],
                'current_second_dose':None,
                'current_symptoms':vaccination_json[0]['symptoms'],
                'current_completed_doses':int(vaccination_json[0]['completed_doses']),
                'current_status':vaccination_json[0]['status'],
                'err':message
            }
            # return HttpResponseRedirect('/updateVaccination/'+ssid,context)   
            return render(request, 'application/authenticated/update_vaccination.html',context)

        vaccine = Vaccine.objects.get(brand=vbrand)
        avl_doses_of_vacc = AvailabeVaccines.objects.get(hospital=current_hospital,vaccine=vaccine)
        if status == 'canceled':
            avl_doses_of_vacc.free_amount += vaccine.doses - int(completed_doses)
            avl_doses_of_vacc.reserved -= vaccine.doses + int(completed_doses)
            avl_doses_of_vacc.save()

        #update BigChain
        state = update_vaccination_bigchain(
            current_hospital.public_key,
            current_hospital.private_key,
            ssid,
            vaccine_brand = vbrand,
            status = status,
            completed_doses = completed_doses,
            symptoms = symptoms,
            first_date = dose_a,
            second_date = dose_b
        )
        # print(state)

        current_vaccintaion_bigchain_record = search_amka(amka)
        vaccination_json = json.loads(current_vaccintaion_bigchain_record)
        success_message = "The details have been updated."
        context = {
            'current_amka':vaccination_json[0]['amka'],
            'current_name':vaccination_json[0]['name'],
            'current_age':vaccination_json[0]['age'],
            'current_gender':vaccination_json[0]['gender'],
            'current_country':vaccination_json[0]['country'],
            'current_city':vaccination_json[0]['city'],
            'current_address':vaccination_json[0]['address'],
            'current_vaccine_brand':vaccination_json[0]['vaccine_brand'],
            'current_first_dose':vaccination_json[0]['first_dose_date'],
            'current_second_dose':vaccination_json[0]['second_dose_date'],
            'current_symptoms':vaccination_json[0]['symptoms'],
            'current_completed_doses':int(vaccination_json[0]['completed_doses']),
            'current_status':vaccination_json[0]['status'],
        }
        messages.success(request,success_message)
        return HttpResponseRedirect('/updateVaccination/'+ssid,context)   
    context = {
        'current_amka':vaccination_json[0]['amka'],
        'current_name':vaccination_json[0]['name'],
        'current_age':vaccination_json[0]['age'],
        'current_gender':vaccination_json[0]['gender'],
        'current_country':vaccination_json[0]['country'],
        'current_city':vaccination_json[0]['city'],
        'current_address':vaccination_json[0]['address'],
        'current_vaccine_brand':vaccination_json[0]['vaccine_brand'],
        'current_first_dose':vaccination_json[0]['first_dose_date'],
        'current_second_dose':vaccination_json[0]['second_dose_date'],
        'current_symptoms':vaccination_json[0]['symptoms'],
        'current_completed_doses':int(vaccination_json[0]['completed_doses']),
        'current_status':vaccination_json[0]['status'],
        
    }
    return render(request, 'application/authenticated/update_vaccination.html',context)

@login_required(login_url="login")
def statsPerHospital(request):
    return render(request,'application/authenticated/hospitalStats.html')

def hospitalstats(request):
    return JsonResponse(stats_json_generator('hospital'))  


@login_required(login_url="login")
def statsPerCountry(request):
    return render(request,'application/authenticated/countryStats.html')

def countrystats(request):
    return JsonResponse(stats_json_generator('country'))
    

@login_required(login_url="login")
def statsPerCity(request):
    return render(request,'application/authenticated/cityStats.html')

def citystats(request):
    return JsonResponse(stats_json_generator('city'))

@login_required(login_url="login")
def statsPerAge(request):
    return render(request,'application/authenticated/ageStats.html')

def agestats(request):
    temps = stats_json_generator('age')
    age1 = 0
    age2 = 0
    age3 = 0
    age4 = 0
    print(temps)
    for key in temps.keys():
        print(key)
        if (int(key) < 14): 
            age1 = age1 + int(temps[key]) 
        elif (int(key) < 24): 
            age2 = age2 + int(temps[key]) 
        elif (int(key) < 64): 
            age3 = age3 + int(temps[key]) 
        else:
            age4 = age4 + int(temps[key]) 

    final = {
        "0-14" : age1,
        "15-24": age2,
        "25-64": age3,
        "65+"  : age4
    }
    print(final)
    return JsonResponse(final, safe=False)    
    
def stats_json_generator(field):
    all = search_status('completed')
    returned_json = {}
    temp_list_of_found_fields = []

    #metatropi toy all se json
    json_all = json.loads(all)

    #dinamika vrisko poses diaforetikes eggrafes iparoyn gia to pedio field
    for item in json_all:
        temp_list_of_found_fields.append(item[field])
    
    set_temp_list_of_found_fieldsset = set(temp_list_of_found_fields)
    #gia kathe diaforetiki eggrafi metrao poses fores vrethike sto json
    for setitem in set_temp_list_of_found_fieldsset:
        count_json_records = 0
        for listitem in temp_list_of_found_fields:
            if listitem == setitem:
                count_json_records+=1

        returned_json[setitem] = count_json_records

    return returned_json


@login_required(login_url="login")
def all_vaccinations_data(request):
    all_vaccination_records = search_all()
    all_vaccination_records_json = json.loads(all_vaccination_records)
    return JsonResponse(all_vaccination_records_json,safe=False)

@login_required(login_url="login")
def all_vaccinations(request):
    all_vaccination_records = search_all()
    all_vaccination_records_json = json.loads(all_vaccination_records)
    current_user = request.user
    current_hospital = Hospital.objects.get(user=current_user)
    context = {
        'current_hospital':current_hospital,
        'all_vaccination_records_json':all_vaccination_records_json
    }
    return render(request,'application/authenticated/all_vaccinations.html',context)
