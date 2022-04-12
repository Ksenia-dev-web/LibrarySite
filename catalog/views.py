from django.shortcuts import render
import requests
from .models import Book, Author, BookInstance, Genre
from django.contrib.auth.decorators import login_required, permission_required
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
import datetime
from .forms import RenewBookForm


# @login_required()
# @permission_required('catalog.can_mark_returned')
# @permission_required(('catalog.can_edit'))
def index(request):
    # generate counts of some of the main objects
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()

    num_instances_available = BookInstance.objects.filter(status__exact='a').count()

    # the 'all()' is implied by default
    num_authors = Author.objects.count()
    num_genres = Genre.objects.count()
    # num_books_with_word = Book.objects.filter(title__icontains='Маргарита').count()
    # number of visits to this view, as counted in the session variable
    num_visits = request.session.get('num_visits', 1)
    request.session['num_visits'] = num_visits + 1

    context = {
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_genres': num_genres,
        # 'num_books_with_word': num_books_with_word,
        'num_visits': num_visits,
    }
    return render(request, 'index.html', context=context)


class BookListView(generic.ListView):
    model = Book
    paginate_by = 10

    # context_object_name = 'my_book_list'
    # # get five catalog containing the title war
    # # queryset = Book.objects.filter(title__icontains='war'[:5])
    # template_name = 'catalog/book_list.html'
    #
    # def get_queryset(self, **kwargs):
    #     context = super(BookListView, self).get_context_data(**kwargs)
    #     # create any data and add it to the context
    #     context['some data'] = 'This is some data'
    #     return context
        # return Book.objects.filter(title__icontains='war')[:5]


class BookDetailView(generic.DetailView):
    model = Book


# def book_detail_view(request, primary_key):
#     try:
#         book = Book.objects.get(pk=primary_key)
#     except Book.DoesNotExist:
#         raise Http404('Book does not exist')
#
#     return render(request, 'book_detail.html', context={'book': book})

class AuthorDetailView(generic.DetailView):
    model = Author


class AuthorListView(generic.ListView):
    model = Author
    paginate_by = 10


class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
    """Generic class-based view listing books on loan to current user."""
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).\
            filter(status__exact='o').order_by('due_back')


class LoanedBooksAllListView(PermissionRequiredMixin, generic.ListView):
    """Generic class-based view listing books on loan to current user."""
    model = BookInstance
    permission_required = 'catalog.can_mark_returned'
    template_name = 'catalog/bookinstance_list_borrowed_all.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(status__exact='o').order_by('due_back')


@login_required
@permission_required('catalog.can_mark_returned', raise_exception=True)
def renew_book_librarian(request, pk):
    book_instance = get_object_or_404(BookInstance, pk=pk)
    if request.method == "POST":
        form = RenewBookForm(request.POST)
        if form.is_valid():
            book_instance.due_back = form.cleaned_data['renewal_date']
            book_instance.save()
            return HttpResponseRedirect(reverse('all-borrowed'))
        # if this is a GET (or any other method) create the default form
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date,})
    return render(request, 'catalog/book_renew_librarian.html', {'form': form, 'book_instance': book_instance})


# class RenewBookModelForm(ModelForm):
#     def clean_due_back(self):
#        data = self.cleaned_data['due_back']
#
#        #Проверка того, что дата не в прошлом
#        if data < datetime.date.today():
#            raise ValidationError(_('Invalid date - renewal in past'))
#
#        #Check date is in range librarian allowed to change (+4 weeks)
#        if data > datetime.date.today() + datetime.timedelta(weeks=4):
#            raise ValidationError(_('Invalid date - renewal more than 4 weeks ahead'))
#
#        # Не забывайте всегда возвращать очищенные данные
#        return data
#
#     class Meta:
#         model = BookInstance
#         fields = ['due_back',]
#         labels = { 'due_back': _('Renewal date'), }
#         help_texts = { 'due_back': _('Enter a date between now and 4 weeks (default 3).'), }


class AuthorCreate(CreateView):
    model = Author
    fields = '__all__'
    initial = {'date_of_death': '12/10/2016',}


class AuthorUpdate(UpdateView):
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']


class AuthorDelete(DeleteView):
    model = Author
    success_url = reverse_lazy('authors')


class BookCreate(PermissionRequiredMixin, CreateView):
    model = Book
    fields = ['title', 'author', 'summary', 'isbn', 'genre', 'language']
    permission_required = 'catalog.can_mark_returned'


class BookUpdate(PermissionRequiredMixin, UpdateView):
    model = Book
    fields = ['title', 'author', 'summary', 'isbn', 'genre', 'language']
    permission_required = 'catalog.can_mark_returned'


class BookDelete(PermissionRequiredMixin, DeleteView):
    model = Book
    success_url = reverse_lazy('books')
    permission_required = 'catalog.can_mark_returned'
