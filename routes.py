from flask import render_template, request, redirect, url_for, send_file, flash, current_app, jsonify
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from database import db, User, UserAnswer, Question
from forms import (RegistrationForm, LoginForm, PersonalInformationForm, ChangePasswordForm, 
                   ContactForm, ContactConfirmForm, AccountDeletionForm, AnswerForm, 
                   ReportForm, PasswordResetRequestForm, DeleteAnswerForm, 
                   AdminAddForm, AdminRemoveForm)
from services import UserService, QuestionService, AnswerService, ReportService
from email_service import EmailService
from country_data import COUNTRY_CHOICES
import os
import datetime

COUNTRY_NAME_BY_CODE = dict(COUNTRY_CHOICES)
COUNTRY_CODE_BY_NAME = {name: code for code, name in COUNTRY_CHOICES}


def register_routes(app):
    """Register all routes"""
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(User, user_id)
        except Exception as e:
            print(f"Error loading user {user_id}: {e}")
            return None
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template(
            '404.html',
            logged_in=current_user.is_authenticated,
            name=current_user.username if current_user.is_authenticated else None
        ), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template(
            'errors/500.html',
            logged_in=current_user.is_authenticated,
            name=current_user.username if current_user.is_authenticated else None
        ), 500
    
    # Main pages
    @app.route('/')
    def home():
        """Home page"""
        # Get random question
        user_id = current_user.id if current_user.is_authenticated else None
        random_question = QuestionService.get_random_question(user_id)
        
        if not random_question:
            flash("No questions available.")
            random_question = {'id': 0, 'question': 'No questions available', 'category': 'unknown', 'depth': 'unknown'}
        
        # Handle logged-in user tabs
        if current_user.is_authenticated:
            page = request.args.get('page', 1, type=int)
            tab = request.args.get('tab', 'my_answers')
            category_filter = request.args.get('category')
            depth_filter = request.args.get('depth')
            sort_order = 'desc' if request.args.get('sort') != 'oldest' else 'asc'

            if tab == 'public_answers':
                result = AnswerService.get_public_answers(
                    current_user.id,
                    page=page,
                    per_page=current_app.config['POSTS_PER_PAGE'],
                    category_filter=category_filter,
                    depth_filter=depth_filter,
                    sort_order=sort_order
                )
            else:
                result = AnswerService.get_user_answers(
                    current_user.id,
                    page=page,
                    per_page=current_app.config['POSTS_PER_PAGE'],
                    category_filter=category_filter,
                    depth_filter=depth_filter,
                    sort_order=sort_order
                )

            user_stats = UserService.get_user_stats(current_user.id)
            delete_form = DeleteAnswerForm()
            
            return render_template(
                'index.html',
                question=random_question,
                category=current_app.config['CATEGORY'],
                depth=current_app.config['DEPTH'],
                user_data=result['answers'],
                pages=result['total_pages'],
                current_page=result['current_page'],
                current_tab=tab,
                current_category=category_filter,
                current_depth=depth_filter,
                current_sort=request.args.get('sort', 'latest'),
                logged_in=True,
                name=current_user.username,
                user_stats=user_stats,
                delete_form=delete_form
            )
        else:
            return render_template(
                'index.html',
                question=random_question,
                category=current_app.config['CATEGORY'],
                depth=current_app.config['DEPTH'],
                logged_in=False,
                name=None,
                delete_form=None
            )
    
    # Individual answer view
    @app.route('/post=<answer_id>')
    def view_answer(answer_id):
        """View individual answer"""
        try:
            # Parse answer ID (remove leading zeros if present)
            actual_id = int(answer_id.lstrip('0')) if answer_id != '0' else 0
        except ValueError:
            flash("Invalid answer ID.")
            return redirect(url_for('home'))
        
        # Check if user is logged in
        if not current_user.is_authenticated:
            # For non-logged users, only show public answers
            answer_data = AnswerService.get_answer_with_question(actual_id)
            if not answer_data or answer_data.get('is_public') != 1:
                flash("Answer not found or not accessible.")
                return redirect(url_for('home'))
            
            is_own_answer = False
        else:
            # For logged-in users, first try to get their own answer by question_id
            # Get the question_id from the answer first
            try:
                answer_record = db.session.query(UserAnswer).filter(UserAnswer.id == actual_id).first()
                if not answer_record:
                    flash("Answer not found.")
                    return redirect(url_for('home'))
                    
                # Check if this is the user's own answer
                if answer_record.user_id == current_user.id:
                    # This is user's own answer, get full data for editing
                    answer_data = AnswerService.get_answer_for_user(current_user.id, answer_record.question_id)
                    if not answer_data:
                        # Fallback: construct answer data from the record
                        question = QuestionService.get_question_by_id(answer_record.question_id)
                        if question:
                            answer_data = {
                                'id': answer_record.id,
                                'user_id': answer_record.user_id,
                                'question_id': answer_record.question_id,
                                'question': answer_record.question,
                                'answer': answer_record.answer,
                                'is_public': answer_record.is_public,
                                'created_at': answer_record.created_at,
                                'updated_at': answer_record.updated_at,
                                'category': question['category'],
                                'depth': question['depth'],
                                'username': current_user.username
                            }
                        else:
                            flash("Question data not found.")
                            return redirect(url_for('home'))
                    is_own_answer = True
                else:
                    # Not user's own answer, check if it's a public answer
                    answer_data = AnswerService.get_answer_with_question(actual_id)
                    if not answer_data or answer_data.get('is_public') != 1:
                        flash("Answer not found.")
                        return redirect(url_for('home'))
                    is_own_answer = False
            except Exception as e:
                print(f"Error retrieving answer: {e}")
                flash("Answer not found.")
                return redirect(url_for('home'))
        
        if not answer_data:
            flash("Answer not found.")
            return redirect(url_for('home'))
        
        return render_template(
            'view_answer.html',
            answer=answer_data,
            is_own_answer=is_own_answer,
            logged_in=current_user.is_authenticated,
            name=current_user.username if current_user.is_authenticated else None
        )

    # Question refresh (AJAX)
    @app.route('/refresh_question')
    @login_required
    def refresh_question():
        """Get new question"""
        exclude_id = request.args.get('exclude', type=int)
        new_question = QuestionService.get_random_question(current_user.id, exclude_id)
        
        if new_question:
            return jsonify({'success': True, 'question': new_question})
        else:
            return jsonify({'success': False, 'message': 'No questions available'})
    
    # Filter routes (redirects)
    @app.route('/cat=<category>')
    def filtered_category(category):
        """Category filter"""
        tab = request.args.get('tab', 'my_answers')
        return redirect(url_for('home', category=category, page=1, tab=tab))
    
    @app.route('/depth=<depth>')
    def filtered_depth(depth):
        """Depth filter"""
        tab = request.args.get('tab', 'my_answers')
        return redirect(url_for('home', depth=depth, page=1, tab=tab))
    
    @app.route('/sort=<sort>')
    def sort_posts(sort):
        """Sort posts"""
        tab = request.args.get('tab', 'my_answers')
        return redirect(url_for('home', sort=sort, page=1, tab=tab))
    
    @app.route('/page=<int:number>')
    def pagination(number):
        """Pagination"""
        tab = request.args.get('tab', 'my_answers')
        return redirect(url_for('home', page=number, tab=tab))
    
    # Answer operations
    @app.route('/post=<int:question_id>', methods=["POST"])
    @login_required
    def submit_answer(question_id):
        """Submit answer"""
        if request.method == "POST":
            answer_text = request.form.get("new_record")
            is_public = 1 if request.form.get("is_public") == "1" else 0

            if answer_text:
                success, message = AnswerService.create_answer(
                    current_user.id, question_id, answer_text, current_user.student, is_public
                )
                flash(message)
            else:
                flash("Please enter an answer.")
        return redirect(url_for("home"))
    
    @app.route('/edit=<int:question_id>', methods=["GET", "POST"])
    @login_required
    def edit_answer(question_id):
        """Edit answer"""
        if request.method == "POST":
            answer_text = request.form.get("new_record")
            is_public = 1 if request.form.get("is_public") == "1" else 0

            if answer_text:
                success, message = AnswerService.update_answer(
                    current_user.id, question_id, answer_text, is_public
                )
                flash(message)
                return redirect(url_for("home"))
            else:
                flash("Please enter an answer.")
        
        # GET request - show edit form
        answer_data = AnswerService.get_answer_for_edit(current_user.id, question_id)
        if not answer_data:
            flash("Answer not found.")
            return redirect(url_for("home"))
        
        return render_template(
            "edit.html",
            question=answer_data,
            logged_in=True,
            name=current_user.username
        )
    
    @app.route('/delete=<int:question_id>', methods=["POST"])
    @login_required
    def delete_answer(question_id):
        """Delete answer"""
        form = DeleteAnswerForm()
        if not form.validate_on_submit():
            flash("Invalid delete request.")
            return redirect(url_for("home"))
        
        success, message = AnswerService.delete_answer(current_user.id, question_id)
        flash(message)
        return redirect(url_for("home"))
    
    # Report functionality
    @app.route('/report=<int:answer_id>', methods=["GET", "POST"])
    @login_required
    def report_answer(answer_id):
        """Report answer"""
        # Get the answer data first
        answer_data = AnswerService.get_answer_with_question(answer_id)
        if not answer_data:
            flash("Answer not found.")
            return redirect(url_for("home", tab="public_answers"))
        
        # Check if user is trying to report their own answer
        if answer_data['user_id'] == current_user.id:
            flash("You cannot report your own answer.")
            return redirect(url_for("home", tab="public_answers"))
        
        form = ReportForm()
        if form.validate_on_submit():
            reason = form.reason.data
            additional_info = form.additional_info.data
            full_reason = f"{reason}"
            if additional_info:
                full_reason += f": {additional_info}"
            
            success, message = ReportService.create_report(
                current_user.id, answer_id, full_reason
            )
            
            if success:
                try:
                    # Extract report ID from success message
                    report_id = "Unknown"
                    if "#" in message:
                        report_id = message.split("#")[1].split()[0]
                    
                    report_data = {
                        "report_id": report_id,
                        "reporter_username": current_user.username,
                        "reporter_email": current_user.email,
                        "reported_answer_id": answer_id,
                        "reported_username": answer_data['username'],
                        "question": answer_data['question'],
                        "answer": answer_data['answer'],
                        "reason": full_reason,
                        "created_at": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    email_service = EmailService()
                    
                    # Check if email service is properly configured
                    if not email_service.from_email:
                        flash(f"{message} (Note: Email notifications are not configured)")
                        return redirect(url_for("home", tab="public_answers"))
                    
                    if not email_service.password:
                        flash(f"{message} (Note: Email notifications are not configured)")
                        return redirect(url_for("home", tab="public_answers"))
                    
                    # Send emails
                    email_success, email_message = email_service.send_report_notification_email(report_data)
                    
                    if not email_success:
                        flash(f"Email notification error: {email_message}")
                
                except Exception:
                    current_app.logger.exception("Email service error for report")
                    flash("Email notification error.")
            
            flash(message)
            return redirect(url_for("home", tab="public_answers"))
        
        return render_template(
            "report.html",
            form=form,
            answer=answer_data,
            logged_in=True,
            name=current_user.username
        )
    
    # Authentication routes
    @app.route('/register', methods=["GET", "POST"])
    def register():
        """User registration"""
        form = RegistrationForm()
        if form.validate_on_submit():
            success, message = UserService.create_user(
                form.username.data,
                form.email.data,
                form.password.data,
                form.student.data
            )
            
            if success:
                # Send welcome email
                try:
                    email_service = EmailService()
                    email_success, email_message = email_service.send_welcome_email({
                        "username": form.username.data,
                        "email": form.email.data
                    })
                    if not email_success:
                        print(f"Failed to send welcome email: {email_message}")
                except Exception as e:
                    print(f"Email service error: {e}")
                
                flash(f"Thanks for joining, {form.username.data.title()}! Please login and get started!")
                return redirect(url_for("login"))
            else:
                flash(message)
        
        return render_template('register.html', form=form)
    
    @app.route('/login', methods=["GET", "POST"])
    def login():
        """Login"""
        form = LoginForm()
        if form.validate_on_submit():
            user, error_message = UserService.authenticate_user(
                form.email.data,
                form.password.data
            )
            
            if user:
                login_user(user)
                flash(f"Welcome back, {user.username.title()}!")
                return redirect(url_for("home"))
            else:
                # Add error message above email field instead of flash
                form.email.errors.append(error_message)
        
        return render_template("login.html", form=form)
    
    @app.route('/logout')
    @login_required
    def logout():
        """Logout"""
        logout_user()
        flash("Logged out successfully.")
        return redirect(url_for("home"))
    
    @app.route('/reset_password', methods=["GET", "POST"])
    def reset_password():
        """Password reset request"""
        form = PasswordResetRequestForm()
        if form.validate_on_submit():
            success, result = UserService.request_password_reset(form.email.data)
            
            if success:
                # Send password reset email
                try:
                    user = db.session.execute(
                        db.select(User).where(User.email == form.email.data)
                    ).scalar()
                    
                    if user:
                        email_service = EmailService()
                        email_success, email_message = email_service.send_password_reset_email(
                            user.to_dict(), result
                        )
                        if email_success:
                            flash("Password reset email sent successfully. Please check your inbox.")
                            return redirect(url_for('login'))
                        else:
                            flash(f"Failed to send email: {email_message}")
                    else:
                        flash("User not found.")
                except Exception as e:
                    flash(f"Error sending email: {str(e)}")
            else:
                flash(result)
        
        return render_template("reset_password.html", form=form)
    
    # User management
    @app.route('/mypage')
    @login_required
    def mypage():
        """My page"""
        user_stats = UserService.get_user_stats(current_user.id)
        
        return render_template(
            "mypage.html",
            logged_in=True,
            name=current_user.username,
            user_stats=user_stats
        )
    
    @app.route('/personal_information', methods=["GET", "POST"])
    @login_required
    def personal_information():
        """Personal information update"""
        form = PersonalInformationForm()
        
        # Set form data on GET request
        if request.method == 'GET':
            form.username.data = current_user.username
            form.email.data = current_user.email
            form.student.data = current_user.student
            if current_user.birthday:
                try:
                    form.birthday.data = datetime.datetime.strptime(current_user.birthday, '%Y-%m-%d').date()
                except:
                    pass
            form.pronouns.data = current_user.pronouns or ''
            stored_location = current_user.location or ''
            if stored_location:
                if stored_location in COUNTRY_NAME_BY_CODE:
                    form.location.data = stored_location
                else:
                    form.location.data = COUNTRY_CODE_BY_NAME.get(stored_location, '')
            else:
                form.location.data = ''

        if form.validate_on_submit():
            update_data = {
                "username": form.username.data,
                "email": form.email.data,
                "student": int(form.student.data),
                "birthday": form.birthday.data.strftime('%Y-%m-%d') if form.birthday.data else None,
                "pronouns": form.pronouns.data if form.pronouns.data else None,
                "location": form.location.data if form.location.data else None,
            }

            success, message = UserService.update_user(current_user.id, update_data)
            flash(message)
            if success:
                return redirect(url_for('mypage'))
        
        return render_template(
            "personal_information.html",
            form=form,
            logged_in=True,
            name=current_user.username
        )
    
    @app.route('/change_password', methods=["GET", "POST"])
    @login_required
    def change_password():
        """Change password"""
        form = ChangePasswordForm()
        if form.validate_on_submit():
            success, message = UserService.change_password(
                current_user.id, form.new_password.data
            )
            
            if success:
                logout_user()
                flash("Password changed successfully. Please login with your new password.")
                return redirect(url_for("login"))
            else:
                flash(message)
        
        return render_template(
            "password.html",
            form=form,
            logged_in=True,
            name=current_user.username
        )
    
    @app.route('/delete_account', methods=["GET", "POST"])
    @login_required
    def delete_account():
        """Delete account"""
        form = AccountDeletionForm()
        if form.validate_on_submit():
            success, message = UserService.delete_user_account(
                current_user.id, "User requested deletion"
            )
            
            if success:
                logout_user()
                flash("Your account has been successfully deleted.")
                return redirect(url_for("home"))
            else:
                flash(message)
        
        return render_template(
            "delete_account.html",
            form=form,
            logged_in=True,
            name=current_user.username
        )
    
    @app.route('/download')
    @login_required
    def download():
        """Data download"""
        filename, message = AnswerService.export_user_data(current_user.id)
        
        if filename:
            try:
                return send_file(path_or_file=filename, as_attachment=True)
            finally:
                # Delete file after download
                if os.path.exists(filename):
                    os.remove(filename)
                flash("Downloaded successfully.")
        else:
            flash(message)
            return redirect(url_for('mypage'))
    
    # Contact
    @app.route('/contact', methods=["GET", "POST"])
    def contact():
        """Contact form"""
        form = ContactForm()
        if form.validate_on_submit():
            inquiry_data = {
                "name": form.name.data,
                "email": form.email.data,
                "category": form.category.data,
                "message": form.message.data
            }
            
            email_service = EmailService()
            success, message = email_service.send_inquiry_email(inquiry_data)
            flash(message)
            
            if success:
                return redirect(url_for('home'))
        
        return render_template(
            "contact.html",
            form=form,
            logged_in=current_user.is_authenticated,
            name=current_user.username if current_user.is_authenticated else None
        )
    
    # Static pages
    @app.route('/about')
    def about():
        """About page"""
        return render_template(
            "about.html",
            logged_in=current_user.is_authenticated,
            name=current_user.username if current_user.is_authenticated else None
        )
    
    @app.route('/help')
    def help():
        """Help page"""
        return render_template(
            "help.html",
            logged_in=current_user.is_authenticated,
            name=current_user.username if current_user.is_authenticated else None
        )
    
    @app.route('/terms_of_use')
    def terms_of_use():
        """Terms of use page"""
        return render_template(
            "terms_of_use.html",
            logged_in=current_user.is_authenticated,
            name=current_user.username if current_user.is_authenticated else None
        )
    
    # Legacy routes for compatibility
    @app.route('/settings', methods=["GET", "POST"])
    @login_required
    def settings():
        """Settings (redirect to personal information)"""
        return redirect(url_for('personal_information'))

    @app.route('/reset', methods=["GET", "POST"])
    @login_required
    def reset():
        """Password reset (redirect to change password)"""
        return redirect(url_for('change_password'))

    # Admin routes
    @app.route('/ms-admin-settings')
    @login_required
    def admin_settings():
        """Admin settings page (only accessible to admins)"""
        # Check if user is admin
        if not current_user.admin:
            flash("Unauthorized access.")
            return redirect(url_for('home'))
        
        # Get reported answers sorted by report count
        reported_answers = db.session.execute(
            db.select(UserAnswer)
            .where(UserAnswer.report_count > 0)
            .order_by(UserAnswer.report_count.desc())
            .limit(50)
        ).scalars().all()
        
        # Get statistics
        from sqlalchemy import func
        today = datetime.datetime.now().date()
        yesterday = today - datetime.timedelta(days=1)
        
        # Today's answers
        today_answers = db.session.execute(
            db.select(func.count(UserAnswer.id))
            .where(func.date(UserAnswer.created_at) == today)
        ).scalar() or 0
        
        # Active users in last 24 hours
        active_24h = db.session.execute(
            db.select(func.count(User.id.distinct()))
            .where(User.last_login_at >= (datetime.datetime.now() - datetime.timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S'))
        ).scalar() or 0
        
        # Total users
        total_users = db.session.execute(
            db.select(func.count(User.id))
        ).scalar() or 0

        # Public posts
        public_posts = db.session.execute(
            db.select(func.count(UserAnswer.id))
            .where(UserAnswer.is_public == 1)
        ).scalar() or 0
        
        # Private posts
        private_posts = db.session.execute(
            db.select(func.count(UserAnswer.id))
            .where(UserAnswer.is_public == 0)
        ).scalar() or 0
        
        # Total answers
        total_answers = db.session.execute(
            db.select(func.count(UserAnswer.id))
        ).scalar() or 0
        
        stats = {
            'today_answers': today_answers,
            'active_users_24h': active_24h,
            'total_users': total_users,
            'public_posts': public_posts,
            'private_posts': private_posts,
            'total_answers': total_answers
        }

        add_form = AdminAddForm()
        remove_form = AdminRemoveForm()
        
        return render_template(
            'ms_admin_settings.html',
            logged_in=True,
            name=current_user.username,
            reported_answers=reported_answers,
            stats=stats,
            add_form=add_form,
            remove_form=remove_form
        )
    
    @app.route('/admin/add', methods=['POST'])
    @login_required
    def admin_add():
        """Add new admin"""
        # Check if user is admin
        if not current_user.admin:
            flash("Unauthorized access.")
            return redirect(url_for('home'))
        
        form = AdminAddForm()
        if not form.validate_on_submit():
            flash("Invalid request. Please try again.")
            return redirect(url_for('admin_settings'))
        
        email = form.email.data.strip()
        
        # Find user by email
        user = db.session.execute(
            db.select(User).where(User.email == email)
        ).scalar()
        
        if not user:
            flash("User does not exist.")
            return redirect(url_for('admin_settings'))
        
        if user.admin:
            flash("User is already an admin.")
            return redirect(url_for('admin_settings'))
        
        # Make user admin
        db.session.execute(
            db.update(User)
            .where(User.id == user.id)
            .values(admin=1)
        )
        db.session.commit()
        
        flash(f"Successfully added {email} as admin.")
        return redirect(url_for('admin_settings'))
    
    @app.route('/admin/remove', methods=['POST'])
    @login_required
    def admin_remove():
        """Remove admin privileges"""
        # Check if user is admin
        if not current_user.admin:
            flash("Unauthorized access.")
            return redirect(url_for('home'))
        
        form = AdminRemoveForm()
        if not form.validate_on_submit():
            flash("Invalid request. Please try again.")
            return redirect(url_for('admin_settings'))
        
        email = form.email.data.strip()
        
        # Find user by email
        user = db.session.execute(
            db.select(User).where(User.email == email)
        ).scalar()
        
        if not user:
            flash("User does not exist.")
            return redirect(url_for('admin_settings'))
        
        if not user.admin:
            flash("This user is not an admin.")
            return redirect(url_for('admin_settings'))
        
        # Prevent removing yourself
        if user.id == current_user.id:
            flash("You cannot remove your own admin privileges.")
            return redirect(url_for('admin_settings'))
        
        # Remove admin privileges
        db.session.execute(
            db.update(User)
            .where(User.id == user.id)
            .values(admin=0)
        )
        db.session.commit()
        
        flash(f"Successfully removed admin privileges from {email}.")
        return redirect(url_for('admin_settings'))
