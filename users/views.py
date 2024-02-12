from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import UserEditForm, UserProfileForm
from .models import Profile, Department
from django.contrib import messages
from django.views import View
from .forms import DepartmentForm, UpdateDepartmentForm, InputBulkUserForm
from django.contrib.auth.hashers import make_password
import pandas as pd
from django.contrib.auth.models import User, Group


### Department Zone
def list_department(request):
    departments = Department.objects.all().order_by('name')
    context = {
        'departments': departments,
    }
    return render(request, 'users/list_department.html', context)


class InputDepartmentView(View):
    def get(self, request):
        form = DepartmentForm()
        context = {
            'form': form,
        }
        return render(request, 'users/input_department.html', context)

    def post(self, request):
        form = DepartmentForm(request.POST, request.FILES)
        if form.is_valid():
            name = request.POST.get('name')
            name_exist = Department.objects.filter(name=name).exists()
            if name_exist:
                messages.error(request, "Department Name is already taken! Try another one.")
                context = {
                    'form': form,
                }
                return render(request, 'users/input_department.html', context)
            form.save()
            messages.success(request, "Data Department has been saved!")
            form = DepartmentForm()
            context = {
                'form': form,
            }
            return render(request, 'users/input_department.html', context)
        else:
            messages.error(request, "Data invalid. Please try again!")
            form = DepartmentForm(request.POST, request.FILES)
            context = {
                'form': form,
            }
            return render(request, 'users/input_department.html', context)


class UpdateDepartmentView(View):
    def get(self, request, id):
        department = Department.objects.get(id=id)
        form = UpdateDepartmentForm(instance=department)
        context = {
            'form': form,
            'department': department,
        }
        return render(request, 'users/update_department.html', context)

    def post(self, request, id):
        department = Department.objects.get(id=id)
        form = UpdateDepartmentForm(request.POST, request.FILES, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, "Data Department has been updated!")
            return redirect('users:list_department')
        else:
            form = UpdateDepartmentForm(instance=department)
            messages.error(request, "Data Department is invalid! Please try again.")
            context = {
                'form': form,
                'department': department,
            }
            return render(request, 'users/update_department.html', context)


class DeleteDepartmentView(View):
    def get(self, request, id):
        department = Department.objects.get(id=id)
        context = {
            'department': department,
        }
        return render(request, 'users/delete_department.html', context)

    def post(self, request, id):
        department = Department.objects.get(id=id)
        department.delete()
        messages.success(request, "Data Department has been deleted.")
        return redirect('users:list_department')


#
@login_required
def edit_profile(request):
    user_profile = Profile.objects.get(profile2user=request.user)
    if request.method == 'POST':
        profile_form = UserProfileForm(
            request.POST, request.FILES, instance=request.user.user2profile)

        if profile_form.is_valid():
            profile_form.save()
            if user_profile.full_name != request.user.first_name + ' ' + request.user.last_name:
                user_profile.full_name = request.user.first_name + ' ' + request.user.last_name
                user_profile.save()
            messages.success(request, "Profile has been updated.")
            return redirect('pica:dashboard')
        else:
            messages.error(request, "Invalid Data, please try again.")

    else:
        profile_form = UserProfileForm(instance=request.user.user2profile)

    context = {
        'profile_form': profile_form,
        'user_profile': user_profile,
    }
    return render(request,
                  'users/update_profile.html', context)


class InputBulkUsersView(View):
    def get(self, request):
        form = InputBulkUserForm()
        context = {
            'form': form,
        }
        return render(request, 'users/input_bulk_user.html', context)

    def post(self, request):
        form = InputBulkUserForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            cd = form.cleaned_data
            df = pd.read_csv(cd['file_content'])
            for index, row in df.iterrows():
                username = row['Username']
                first_name = row['FirstName']
                last_name = row['LastName']
                email = row['Email']
                password = make_password("epica2024")
                User.objects.update_or_create(username=username, first_name=first_name.title(),
                                              last_name=last_name.title(),
                                              email=email.lower(),
                                              password=password)
            for index, row in df.iterrows():
                username = row['Username']
                BOD = row['BODStatus']
                CPMD = row['CPMDStatus']
                SECRETARY = row['SECTStatus']
                PIC = row['PIC']
                PIC_EPICA = row['PICEpica']
                current_user = User.objects.get(username=username)
                user_profile = Profile.objects.get(profile2user=current_user)
                # Take all groups
                grp_bod = Group.objects.get(name="BOD")
                grp_secretary = Group.objects.get(name="Secretary")
                grp_cpmd = Group.objects.get(name="CPMD")
                grp_pic = Group.objects.get(name="PIC")
                grp_pic_epica = Group.objects.get(name="PIC ePica")
                if BOD == "Y":
                    user_profile.bod = "Y"
                    current_user.groups.add(grp_bod)
                else:
                    user_profile.bod = "N"
                if CPMD == "Y":
                    user_profile.cpmd = "Y"
                    current_user.groups.add(grp_cpmd)
                else:
                    user_profile.cpmd = "N"
                if SECRETARY == "Y":
                    user_profile.secretary = "Y"
                    current_user.groups.add(grp_secretary)
                else:
                    user_profile.secretary = "N"
                if PIC == "Y":
                    user_profile.pic = "Y"
                    current_user.groups.add(grp_pic)
                else:
                    user_profile.pic = "N"
                if PIC_EPICA == "Y":
                    user_profile.pic_epica = "Y"
                    current_user.groups.add(grp_pic_epica)
                else:
                    user_profile.pic_epica = "N"
                user_profile.full_name = current_user.first_name.title() + " " + current_user.last_name.title()
                user_profile.save()
                current_user.save()
            messages.success(request, "Input Bulk Users has been processed")
            return redirect('pica:home')
        else:
            print(form.errors)
            print(form.fields)
            messages.error(request, "Data is not valid!")
            form = InputBulkUserForm()
            context = {
                'form': form,
            }
            return render(request, 'users/input_bulk_user.html', context)
