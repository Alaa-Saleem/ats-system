from django.db import models
from django.conf import settings
from django.urls import reverse

class Client(models.Model):
    name = models.CharField(max_length=255, verbose_name="اسم الشركة")
    industry = models.CharField(max_length=255, blank=True, verbose_name="مجال العمل")
    website = models.URLField(blank=True, verbose_name="الموقع الإلكتروني")
    phone = models.CharField(max_length=50, blank=True, verbose_name="رقم الهاتف")
    email = models.EmailField(blank=True, verbose_name="البريد الإلكتروني")
    address = models.TextField(blank=True, verbose_name="العنوان")
    notes = models.TextField(blank=True, verbose_name="ملاحظات")
    
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='clients',
        verbose_name="المسؤول"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        db_table = 'clients'
        ordering = ['-created_at']
        verbose_name = "عميل"
        verbose_name_plural = "العملاء"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('clients:detail', kwargs={'pk': self.pk})


class ClientContact(models.Model):
    client = models.ForeignKey(
        Client, 
        on_delete=models.CASCADE, 
        related_name='contacts',
        verbose_name="الشركة"
    )
    name = models.CharField(max_length=255, verbose_name="اسم جهة الاتصال")
    title = models.CharField(max_length=255, blank=True, verbose_name="المسمى الوظيفي")
    phone = models.CharField(max_length=50, blank=True, verbose_name="رقم الهاتف")
    email = models.EmailField(blank=True, verbose_name="البريد الإلكتروني")
    is_primary = models.BooleanField(default=False, verbose_name="جهة الاتصال الرئيسية")
    
    class Meta:
        db_table = 'client_contacts'
        ordering = ['-is_primary', 'name']
        verbose_name = "جهة اتصال"
        verbose_name_plural = "جهات الاتصال"

    def __str__(self):
        return f"{self.name} - {self.client.name}"
