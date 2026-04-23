from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse_lazy
from .models import Client, ClientContact
from .forms import ClientForm

class ClientAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser


class ClientListView(ClientAccessMixin, ListView):
    model = Client
    template_name = 'clients/client_list.html'
    context_object_name = 'clients'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.role != "admin":
            queryset = queryset.filter(owner=self.request.user)
        query = self.request.GET.get('q')
        
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(industry__icontains=query) |
                Q(phone__icontains=query) |
                Q(email__icontains=query)
            )
        return queryset

class ClientCreateView(ClientAccessMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = 'clients/client_form.html'
    success_url = reverse_lazy('clients:list')
    
    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'تم إضافة الشركة {self.object.name} بنجاح')
        return response

class ClientUpdateView(ClientAccessMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = 'clients/client_form.html'
    
    def get_success_url(self):
        return reverse_lazy('clients:detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'تم تحديث بيانات الشركة {self.object.name}')
        return response

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.role != "admin":
            queryset = queryset.filter(owner=self.request.user)
        return queryset

class ClientDetailView(ClientAccessMixin, DetailView):
    model = Client
    template_name = 'clients/client_detail.html'
    context_object_name = 'client'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['contacts'] = self.object.contacts.all()
        # You could also add jobs related to this client here in the future
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.role != "admin":
            queryset = queryset.filter(owner=self.request.user)
        return queryset
