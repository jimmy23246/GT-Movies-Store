from django.shortcuts import render, redirect, get_object_or_404
from .models import Movie, Review, ReviewReaction
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db.models import Count
from django.contrib.auth.models import User




# Create your views here.
def index(request):
    search_term = request.GET.get('search')

    if search_term:
        movies = Movie.objects.filter(name__icontains=search_term)
    else:
        movies = Movie.objects.all()
    
    template_data = {}
    template_data['title'] = 'Movies'
    template_data['movies'] = movies

    return render(request, 'movies/index.html', {'template_data': template_data})

def show(request, id):
    movie = Movie.objects.get(id=id)
    reviews = (Review.objects
           .filter(movie=movie)
           .annotate(score=Count('reactions'))
           .order_by('-date'))

    template_data = {}
    template_data['title'] = movie.name
    template_data['movie'] = movie
    template_data['reviews'] = reviews

    return render(request, 'movies/show.html', {'template_data': template_data})

@login_required
def create_review(request, id):
    if request.method == 'POST' and request.POST['comment'] != '':
        movie = Movie.objects.get(id=id)
        review = Review()
        review.comment = request.POST['comment']
        review.movie = movie
        review.user = request.user
        review.save()
        return redirect('movies.show', id=id)
    else:
        return redirect('movies.show', id=id)

@login_required
def edit_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id)
    if request.user != review.user:
        return redirect('movies.show', id=id)
    if request.method == 'GET':
        template_data = {}
        template_data['title'] = 'Edit Review'
        template_data['review'] = review
        return render(request, 'movies/edit_review.html',
            {'template_data': template_data})
    elif request.method == 'POST' and request.POST['comment'] != '':
        review = Review.objects.get(id=review_id)
        review.comment = request.POST['comment']
        review.save()
        return redirect('movies.show', id=id)
    else:
        return redirect('movies.show', id=id)
    
@login_required
def delete_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id,
        user=request.user)
    review.delete()
    return redirect('movies.show', id=id)


def top_comments(request):
    # 댓글에 달린 반응 개수를 score로 주석(annotate)
    reviews = (Review.objects
               .select_related('user', 'movie')
               .annotate(score=Count('reactions'))
               .order_by('-score', '-date'))

    # 유저 랭킹(가장 ‘웃긴’ 유저): 본인이 쓴 댓글의 총 업보트 수
    top_users = (User.objects
                 .filter(review__isnull=False)
                 .annotate(total_upvotes=Count('review__reactions'))
                 .order_by('-total_upvotes', 'username')[:10])

    template_data = {
        'title': 'Top Comments',
        'reviews': reviews,
        'top_users': top_users,
    }
    return render(request, 'movies/top_comments.html', {'template_data': template_data})


@login_required
def toggle_review_upvote(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    rr, created = ReviewReaction.objects.get_or_create(review=review, user=request.user)
    if not created:
        # 이미 추천했으면 해제(토글)
        rr.delete()
    # 돌아갈 곳: referrer가 있으면 거기로, 없으면 해당 영화 상세
    next_url = request.META.get('HTTP_REFERER') or reverse('movies.show', kwargs={'id': review.movie.id})
    return redirect(next_url)

