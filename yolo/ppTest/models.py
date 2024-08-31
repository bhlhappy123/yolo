from django.db import models
from django.contrib.auth import get_user_model

# Create your models here.


User = get_user_model()


class images_input(models.Model):
    username = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户名')
    pub_time = models.DateTimeField(auto_now_add=True, verbose_name='上传时间')


class images_output(models.Model):
    username = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户名')
    pub_time = models.DateTimeField(auto_now_add=True, verbose_name='检测时间')

    class Meta:
        # apple, apples
        verbose_name = '检测图片'
        verbose_name_plural = verbose_name
        ordering = ['-pub_time']
