import os
from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app
from flask_login import current_user, login_required
from flask_babel import _, get_locale
from langdetect import detect, LangDetectException
from app import db
from app.main.forms import EditProfileForm, EmptyForm, PostForm
from app.models import User, Post
from app.translate import translate
from app.main import bp



@bp.route('/', methods=['POST', 'GET'])
@bp.route('/index', methods=['POST', 'GET'])
@login_required
def index():
    form = PostForm()
    print(os.environ.get('MAIL_SERVER'))
    print( os.environ)
    print(os.environ.get('MS_TRANSLATOR_KEY'))

    if form.validate_on_submit():
        try:
            language = detect(form.post.data)
        except LangDetectException:
            language = ''

        post = Post(body=form.post.data, author=current_user, language=language)

        db.session.add(post)
        db.session.commit()
        flash(_('Your post is now live!'))
        return redirect(url_for('main.index'))

    if request.method == 'GET':

        page = request.args.get('page', 1, type=int)
        posts = current_user.followed_posts().paginate(page, 3, False)

        next_url = url_for('main.index', page=posts.next_num)\
            if posts.has_next else None
        print(posts.has_next)
        print(next_url)

        if posts.has_prev:
            prev_url = url_for('main.index', page=posts.prev_num)
        else:
            prev_url = None
        print(prev_url)

        return render_template('index.html', title='home', posts=posts.items, form=form,\
                               next_url=next_url, prev_url=prev_url)



@bp.route('/user/<username>')
@login_required
def user(username):
    form = EmptyForm()
    user = User.query.filter_by(username=username).first_or_404()

    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(page, 3, False)

    next_url = url_for('main.user', username=user.username,  page=posts.next_num) \
        if posts.has_next else None
    print(posts.has_next)
    print(next_url)

    if posts.has_prev:
        prev_url = url_for('main.user', page=posts.prev_num, username=user.username,)
    else:
        prev_url = None
    print(prev_url)


    print(user)
    print(current_user)
    print(current_user.followed.all())
    print(current_user.followers.all())
    print(current_user.followers.first())

    print(current_user.is_following(user))

    return render_template('user.html', user=user, posts=posts.items, form=form,\
                           next_url=next_url, prev_url=prev_url)


@bp.before_request
def before_request():
    if current_user.is_authenticated:

        current_user.last_seen = datetime.utcnow()

        db.session.commit()

        g.locale = str(get_locale())


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():

    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        flash(_('Your changes have been saved.'))
        db.session.commit()
        return redirect(url_for('main.edit_profile'))

    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me

    return render_template('edit_profile.html', title='Edit Profile', form=form)


@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash(_('User {} not found.'.format(username)))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('main.user', username=username))

        current_user.follow(user)
        db.session.commit()
        flash('You are following {}!'.format(username))
        return redirect(url_for('main.user', username=username))

    else:
        return redirect(url_for('main.index'))


@bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():

        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('main.index'))

        if user == current_user:
            flash(_('You cannot unfollow yourself!'))
            return redirect(url_for('main.user', username=username))

        current_user.unfollow(user)
        db.session.commit()
        flash(_('You are not following {}.'.format(username)))
        return redirect(url_for('main.user', username=username))

    else:
        return redirect(url_for('main.index'))


@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(page, 3, False)
    next_url = url_for('main.index', page=posts.next_num) \
        if posts.has_next else None


    if posts.has_prev:
        prev_url = url_for('main.index', page=posts.prev_num)
    else:
        prev_url = None

    return render_template('index.html', title='explore', posts=posts.items,\
                           next_url=next_url, prev_url=prev_url)


@bp.route('/translate', methods=['POST'])
@login_required
def translate_text():
    return jsonify({'text': translate(
        request.form['text'],
        request.form['source_language'],
        request.form['dest_language']
    )})