from django.http import HttpResponse
from django.shortcuts import render, redirect, reverse
from django.http.response import JsonResponse
import string
import random
from django.core.mail import send_mail
from django.views.decorators.clickjacking import xframe_options_exempt

from . import settings
from .models import CaptchaModel
from django.views.decorators.http import require_http_methods
from .forms import RegisterForm, LoginForm
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.models import User
import os
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import subprocess
from . import models

global name
name = None


class USER:
    def __init__(self, username):
        self.username = username

        print(self.username)

    def returnName(self):
        return self.username


@require_http_methods(['GET', 'POST'])
def login_view(request):
    if request.method == 'GET':
        return render(request, 'login.html')
    else:
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            remember = form.cleaned_data.get('remember')
            user = User.objects.filter(email=email).first()
            if user and user.check_password(password):
                # 登录
                login(request, user)
                # 判断是否需要记住我
                if not remember:
                    # 如果没有点击记住我，那么就要设置过期时间为0，即浏览器关闭后就会过期
                    request.session.set_expiry(0)
                # 如果点击了，那么就什么都不做，使用默认的2周的过期时间
                return redirect('/')
            else:
                print('邮箱或密码错误！')
                # form.add_error('email', '邮箱或者密码错误！')
                # return render(request, 'login.html', context={"form": form})
                return redirect(reverse('login_view:login'))


def index_view(request):
    return render(request, 'index.html')


def logout_view(request):
    logout(request)
    return redirect('/')


@require_http_methods(['GET', 'POST'])
def register_view(request):
    if request.method == 'GET':
        return render(request, 'register.html')
    else:
        form = RegisterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            User.objects.create_user(email=email, username=username, password=password)
            return redirect(reverse('login'))
        else:
            print(form.errors)
            # 重新跳转到登录页面
            return redirect(reverse('register'))
            # return render(request, 'register.html', context={"form": form})


def send_email_captcha(request):
    # ?email=xxx
    email = request.GET.get('email')
    if not email:
        return JsonResponse({"code": 400, "message": '必须传递邮箱！'})
    # 生成验证码（取随机的4位阿拉伯数字）
    # ['0', '2', '9', '8']
    captcha = "".join(random.sample(string.digits, 4))
    # 存储到数据库中
    CaptchaModel.objects.update_or_create(email=email, defaults={'captcha': captcha})
    send_mail("注册验证码", message=f"您的注册验证码是：{captcha}", recipient_list=[email], from_email=None)
    return JsonResponse({"code": 200, "message": "邮箱验证码发送成功！"})


def work(request):
    return render(request, 'work.html')


def save_picture_view(request):
    if request.method == 'POST':
        try:
            pic = request.FILES['pic']
            save_path = os.path.join(settings.MEDIA_ROOT, 'AcceptIMG', pic.name)

            # 创建目录如果不存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            with open(save_path, 'wb') as f:
                for chunk in pic.chunks():
                    f.write(chunk)

            print("存储成功", pic.name)

            return JsonResponse({'success': True, 'path': save_path})
        except Exception as e:
            print("保存图片时出错：", e)
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method'})


@xframe_options_exempt
def loading_view(request):
    return render(request, 'loading.html')


@csrf_exempt
@require_POST
def save_forecast_view(request):
    print("request", request)
    print("POST data:", request.POST)
    print("FILES data:", request.FILES)

    if not request.user.is_authenticated:
        return JsonResponse({'status': "请您登录后，再进入系统操作！"})

    file = request.FILES.get('pic')
    if not file:
        return JsonResponse({'status': "未上传图片，请选择图片后再尝试！"})

    # 保存文件到服务器
    file_path = default_storage.save(os.path.join('uploads', file.name), ContentFile(file.read()))
    print("file_path",file_path)
    # 获取保存的文件的绝对路径
    file_path = os.path.join(settings.MEDIA_ROOT, file_path)

    # 运行推理命令
    command = f'python PaddleDetection/tools/infer.py -c configs/rotate/ppyoloe_r/ppyoloe_r_crn_s_3x_spine.yml -o weights=output/ppyoloe_r_crn_s_3x_spine/best_model --infer_img={file_path} --draw_threshold=0.5'
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        print(result.stdout)
        # 假设推理程序会生成一个带有检测结果的图像，命名为 "output.jpg"
        detected_image_path = os.path.join(settings.MEDIA_ROOT, "output.jpg")

        # 返回检测后的图片路径
        return JsonResponse({'path': detected_image_path})

    except subprocess.CalledProcessError as e:
        print(e.stderr)
        return JsonResponse({'status': "预测失败,请重新预测/上传"})

    return JsonResponse({'status': "成功处理图片。"})
