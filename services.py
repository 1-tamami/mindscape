from database import db, User, Question, UserAnswer, DeletedUser, Report
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import and_, func
import datetime as dt
import random
import csv
import math
import secrets
from collections import Counter


class UserService:
    """User-related services"""
    
    @staticmethod
    def create_user(username, email, password, is_student):
        """Create new user"""
        try:
            existing_user = db.session.execute(
                db.select(User).where(User.email == email)
            ).scalar()
            
            if existing_user:
                return False, "Account already exists with this email."
            
            hashed_password = generate_password_hash(
                password, method='pbkdf2:sha256', salt_length=11
            )
            
            new_user = User.create(username, email, hashed_password, is_student)
            db.session.add(new_user)
            db.session.commit()
            
            return True, "Account created successfully."
        except Exception as e:
            db.session.rollback()
            return False, f"Error creating account: {str(e)}"
    
    @staticmethod
    def authenticate_user(email, password):
        """Authenticate user"""
        try:
            user = db.session.execute(
                db.select(User).where(User.email == email)
            ).scalar()
            
            if user:
                if check_password_hash(user.password, password):
                    return user, None
                elif (user.temp_password and 
                      check_password_hash(user.temp_password, password) and
                      user.temp_password_expires and
                      dt.datetime.strptime(user.temp_password_expires, '%Y-%m-%d %H:%M:%S') > dt.datetime.now()):
                    user.is_using_temp_password = 1
                    db.session.commit()
                    return user, None
                else:
                    return None, "Invalid email or password."
            else:
                return None, "Invalid email or password."
        except Exception as e:
            return None, f"Authentication error: {str(e)}"
    
    @staticmethod
    def update_user(user_id, update_data):
        """Update user information"""
        try:
            filtered_data = {k: v for k, v in update_data.items() if v not in [None, ""]}
            
            if not filtered_data:
                return True, "No changes to update."
            
            filtered_data['updated_at'] = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            db.session.execute(
                db.update(User)
                .where(User.id == user_id)
                .values(**filtered_data)
            )
            db.session.commit()
            
            return True, "User information updated successfully."
        except Exception as e:
            db.session.rollback()
            return False, f"Error updating user: {str(e)}"
    
    @staticmethod
    def change_password(user_id, new_password):
        """Change user password"""
        try:
            hashed_password = generate_password_hash(
                new_password, method='pbkdf2:sha256', salt_length=11
            )
            
            db.session.execute(
                db.update(User)
                .where(User.id == user_id)
                .values(
                    password=hashed_password,
                    temp_password=None,
                    temp_password_expires=None,
                    is_using_temp_password=0,
                    updated_at=dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                )
            )
            db.session.commit()
            
            return True, "Password changed successfully."
            
        except Exception as e:
            db.session.rollback()
            return False, f"Error changing password: {str(e)}"
    
    @staticmethod
    def request_password_reset(email):
        """Request password reset"""
        try:
            user = db.session.execute(
                db.select(User).where(User.email == email)
            ).scalar()
            
            if not user:
                return False, "No account found with this email address."
            
            temp_password, expires = user.generate_temp_password()
            hashed_temp_password = generate_password_hash(
                temp_password, method='pbkdf2:sha256', salt_length=11
            )
            
            db.session.execute(
                db.update(User)
                .where(User.id == user.id)
                .values(
                    temp_password=hashed_temp_password,
                    temp_password_expires=expires,
                    is_using_temp_password=0,
                    updated_at=dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                )
            )
            db.session.commit()
            
            return True, temp_password
        except Exception as e:
            db.session.rollback()
            return False, f"Error processing password reset: {str(e)}"
    
    @staticmethod
    def delete_user_account(user_id, deletion_reason=None):
        """Delete user account (anonymize user data while preserving answers)"""
        try:
            user = db.session.execute(
                db.select(User).where(User.id == user_id)
            ).scalar()
            
            if not user:
                return False, "User not found."
            
            # Create deletion record for audit purposes
            deleted_record = DeletedUser(
                original_user_id=user_id,
                deletion_date=dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                deletion_reason=deletion_reason
            )
            db.session.add(deleted_record)
            
            # Process birthday: keep year only, set month and day to 01-01
            anonymized_birthday = None
            if user.birthday:
                try:
                    # Extract year from birthday (format: YYYY-MM-DD)
                    year = user.birthday.split('-')[0]
                    anonymized_birthday = f'{year}-01-01'
                except:
                    anonymized_birthday = None
            
            # Anonymize user data instead of deleting the record
            # This preserves the user_id reference in UserAnswer table
            anonymized_data = {
                'username': f'Contributor {user_id}',
                'email': f'deleted_{user_id}@anonymized.local',
                'password': generate_password_hash(
                    secrets.token_urlsafe(32), method='pbkdf2:sha256', salt_length=11
                ),
                'birthday': anonymized_birthday,
                'pronouns': user.pronouns,  # Keep original pronouns
                'location': None,
                'temp_password': None,
                'temp_password_expires': None,
                'is_using_temp_password': 0,
                # Keep original student value (do not update)
                'updated_at': dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            db.session.execute(
                db.update(User)
                .where(User.id == user_id)
                .values(**anonymized_data)
            )
            
            db.session.commit()
            
            return True, "Account deleted successfully."
        except Exception as e:
            db.session.rollback()
            return False, f"Error deleting account: {str(e)}"
    
    @staticmethod
    def get_user_stats(user_id):
        """Get user statistics"""
        try:
            total_answers = db.session.query(UserAnswer).filter(
                UserAnswer.user_id == user_id
            ).count()
            
            today = dt.datetime.now().strftime('%Y-%m-%d')
            answered_today = db.session.query(UserAnswer).filter(
                and_(
                    UserAnswer.user_id == user_id,
                    UserAnswer.updated_at.like(f'{today}%')
                )
            ).count() > 0
            
            answers_with_questions = db.session.query(
                UserAnswer, Question.category, Question.depth
            ).join(
                Question, UserAnswer.question_id == Question.id
            ).filter(UserAnswer.user_id == user_id).all()
            
            if answers_with_questions:
                categories = [q[1] for q in answers_with_questions]
                depths = [q[2] for q in answers_with_questions]
                
                most_common_category = Counter(categories).most_common(1)[0][0] if categories else None
                most_common_depth = Counter(depths).most_common(1)[0][0] if depths else None
            else:
                most_common_category = None
                most_common_depth = None
            
            return {
                'total_answers': total_answers,
                'answered_today': answered_today,
                'most_common_category': most_common_category,
                'most_common_depth': most_common_depth
            }
        except Exception as e:
            print(f"Error getting user stats: {e}")
            return {
                'total_answers': 0,
                'answered_today': False,
                'most_common_category': None,
                'most_common_depth': None
            }
    



class QuestionService:
    """Question-related services"""
    
    @staticmethod
    def get_random_question(user_id=None, exclude_question_id=None):
        """Get random question (filters out work-related questions for students)"""
        try:
            base_query = db.session.query(Question)
            
            # Check if user is a student
            is_student = False
            if user_id:
                user = db.session.get(User, user_id)
                if user and user.student == 1:
                    is_student = True
                    # Exclude work-related questions for students
                    base_query = base_query.filter(Question.exclude_for_students == 0)
            
            if user_id:
                answered_ids = db.session.query(UserAnswer.question_id).filter(
                    UserAnswer.user_id == user_id
                ).all()
                answered_ids = [item[0] for item in answered_ids]
                
                questions = base_query.filter(
                    ~Question.id.in_(answered_ids)
                ).all()
            else:
                questions = base_query.all()
            
            if exclude_question_id:
                questions = [q for q in questions if q.id != exclude_question_id]
            
            if questions:
                return random.choice([q.to_dict() for q in questions])
            else:
                # If no unanswered questions, return from all questions
                all_questions_query = db.session.query(Question)
                if is_student:
                    all_questions_query = all_questions_query.filter(Question.exclude_for_students == 0)
                
                all_questions = all_questions_query.all()
                if exclude_question_id:
                    all_questions = [q for q in all_questions if q.id != exclude_question_id]
                return random.choice([q.to_dict() for q in all_questions]) if all_questions else None
        except Exception as e:
            print(f"Error getting random question: {e}")
            return None
    
    @staticmethod
    def get_question_by_id(question_id):
        """Get question by ID"""
        try:
            question = db.session.execute(
                db.select(Question).where(Question.id == question_id)
            ).scalar()
            return question.to_dict() if question else None
        except Exception as e:
            print(f"Error getting question: {e}")
            return None


class AnswerService:
    """Answer-related services"""
    
    @staticmethod
    def create_answer(user_id, question_id, answer_text, is_student, is_public=1):
        """Create new answer"""
        try:
            if len(answer_text) > 2000:
                return False, "Answer must be less than 2000 characters."

            question = QuestionService.get_question_by_id(question_id)
            if not question:
                return False, "Question not found."

            new_answer = UserAnswer.create(
                user_id, question_id, question['question'], answer_text, is_student, is_public
            )

            db.session.add(new_answer)
            db.session.commit()

            return True, "Answer submitted successfully."
        except Exception as e:
            db.session.rollback()
            print(f"Error creating answer: {str(e)}")
            return False, f"Error creating answer: {str(e)}"
    
    @staticmethod
    def update_answer(user_id, question_id, answer_text, is_public=None):
        """Update answer"""
        try:
            if len(answer_text) > 2000:
                return False, "Answer must be less than 2000 characters."
            
            update_data = {
                'answer': answer_text,
                'updated_at': dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            if is_public is not None:
                update_data['is_public'] = is_public
            
            db.session.execute(
                db.update(UserAnswer)
                .where(
                    and_(
                        UserAnswer.question_id == question_id,
                        UserAnswer.user_id == user_id
                    )
                )
                .values(**update_data)
            )
            db.session.commit()
            
            return True, "Answer updated successfully."
        except Exception as e:
            db.session.rollback()
            return False, f"Error updating answer: {str(e)}"
    
    @staticmethod
    def delete_answer(user_id, question_id):
        """Delete answer"""
        try:
            answer = db.session.query(UserAnswer).filter(
                UserAnswer.question_id == question_id,
                UserAnswer.user_id == user_id
            ).scalar()
            
            if answer:
                db.session.delete(answer)
                db.session.commit()
                return True, "Answer deleted successfully."
            else:
                return False, "Answer not found."
        except Exception as e:
            db.session.rollback()
            return False, f"Error deleting answer: {str(e)}"
    
    @staticmethod
    def get_user_answers(user_id, page=1, per_page=10, category_filter=None, depth_filter=None, sort_order='desc'):
        """Get user answers list"""
        try:
            query = (
                db.session.query(UserAnswer, Question.category, Question.depth)
                .join(Question, UserAnswer.question_id == Question.id)
                .filter(UserAnswer.user_id == user_id)
            )

            if category_filter and category_filter != "all":
                query = query.filter(Question.category == category_filter)

            if depth_filter and depth_filter != "all":
                query = query.filter(Question.depth == depth_filter)

            if sort_order == 'asc':
                query = query.order_by(UserAnswer.updated_at.asc())
            else:
                query = query.order_by(UserAnswer.updated_at.desc())

            offset = (page - 1) * per_page
            results = query.offset(offset).limit(per_page).all()

            total_count = query.count()
            total_pages = math.ceil(total_count / per_page)

            answers = []
            for user_answer, category, depth in results:
                answer_dict = user_answer.to_dict()
                answer_dict['category'] = category
                answer_dict['depth'] = depth
                answer_dict['padded_id'] = f"{user_answer.id:09d}"
                answers.append(answer_dict)

            return {
                'answers': answers,
                'total_pages': total_pages,
                'current_page': page,
                'total_count': total_count
            }
        except Exception as e:
            print(f"Error getting user answers: {e}")
            return {
                'answers': [],
                'total_pages': 0,
                'current_page': 1,
                'total_count': 0
            }
    
    @staticmethod
    def get_public_answers(current_user_id=None, page=1, per_page=10, category_filter=None, depth_filter=None, sort_order='desc'):
        """Get public answers list"""
        try:
            query = (
                db.session.query(UserAnswer, Question.category, Question.depth, User.username)
                .join(Question, UserAnswer.question_id == Question.id)
                .join(User, UserAnswer.user_id == User.id)
                .filter(UserAnswer.is_public == 1)
            )

            if current_user_id:
                query = query.filter(UserAnswer.user_id != current_user_id)

            if category_filter and category_filter != "all":
                query = query.filter(Question.category == category_filter)

            if depth_filter and depth_filter != "all":
                query = query.filter(Question.depth == depth_filter)

            if sort_order == 'asc':
                query = query.order_by(UserAnswer.updated_at.asc())
            else:
                query = query.order_by(UserAnswer.updated_at.desc())

            offset = (page - 1) * per_page
            results = query.offset(offset).limit(per_page).all()

            total_count = query.count()
            total_pages = math.ceil(total_count / per_page)

            answers = []
            for user_answer, category, depth, username in results:
                answer_dict = user_answer.to_dict()
                answer_dict['category'] = category
                answer_dict['depth'] = depth
                answer_dict['username'] = username
                answer_dict['padded_id'] = f"{user_answer.id:09d}"
                answers.append(answer_dict)

            return {
                'answers': answers,
                'total_pages': total_pages,
                'current_page': page,
                'total_count': total_count
            }
        except Exception as e:
            print(f"Error getting public answers: {e}")
            return {
                'answers': [],
                'total_pages': 0,
                'current_page': 1,
                'total_count': 0
            }
    
    @staticmethod
    def get_answer_with_question(answer_id):
        """Get answer with question details"""
        try:
            result = (
                db.session.query(UserAnswer, Question.category, Question.depth, User.username)
                .join(Question, UserAnswer.question_id == Question.id)
                .join(User, UserAnswer.user_id == User.id)
                .filter(
                    UserAnswer.id == answer_id,
                    UserAnswer.is_public == 1
                )
                .first()
            )
            
            if result:
                user_answer, category, depth, username = result
                answer_dict = user_answer.to_dict()
                answer_dict['category'] = category
                answer_dict['depth'] = depth
                answer_dict['username'] = username
                return answer_dict
            return None
        except Exception as e:
            print(f"Error getting answer with question: {e}")
            return None
    
    @staticmethod
    def export_user_data(user_id):
        """Export user data to CSV"""
        try:
            results = (
                db.session.query(UserAnswer, Question.category, Question.depth)
                .join(Question, UserAnswer.question_id == Question.id)
                .filter(UserAnswer.user_id == user_id)
                .order_by(UserAnswer.updated_at.desc())
                .all()
            )
            
            if not results:
                return None, "No data to export."
            
            filename = f"mindscape_userdata_{dt.datetime.now().strftime('%Y%m%d_%H%M')}.csv"
            
            with open(filename, "w", newline='', encoding='utf-8') as file:
                fieldnames = ['category', 'depth', 'question', 'answer', 'is_public', 'updated_at']
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                
                for user_answer, category, depth in results:
                    writer.writerow({
                        'category': category,
                        'depth': depth,
                        'question': user_answer.question,
                        'answer': user_answer.answer,
                        'is_public': 'Public' if user_answer.is_public else 'Private',
                        'updated_at': user_answer.updated_at
                    })
            
            return filename, "Data exported successfully."
        except Exception as e:
            return None, f"Error exporting data: {str(e)}"
    
    @staticmethod
    def get_answer_for_edit(user_id, question_id):
        """Get answer data for editing"""
        try:
            result = (
                db.session.query(UserAnswer, Question.category, Question.depth)
                .join(Question, UserAnswer.question_id == Question.id)
                .filter(
                    UserAnswer.user_id == user_id,
                    UserAnswer.question_id == question_id
                )
                .first()
            )
            
            if result:
                user_answer, category, depth = result
                answer_dict = user_answer.to_dict()
                answer_dict['category'] = category
                answer_dict['depth'] = depth
                return answer_dict
            return None
        except Exception as e:
            print(f"Error getting answer for edit: {e}")
            return None

    # services.py の AnswerService クラスに以下のメソッドを追加してください

    @staticmethod
    def get_answer_for_user(user_id, question_id):
        """Get user's own answer for a specific question"""
        try:
            result = (
                db.session.query(UserAnswer, Question.category, Question.depth)
                .join(Question, UserAnswer.question_id == Question.id)
                .filter(
                    UserAnswer.user_id == user_id,
                    UserAnswer.question_id == question_id
                )
                .first()
            )
            
            if result:
                user_answer, category, depth = result
                answer_dict = user_answer.to_dict()
                answer_dict['category'] = category
                answer_dict['depth'] = depth
                # Add username for consistency
                user = db.session.get(User, user_id)
                if user:
                    answer_dict['username'] = user.username
                return answer_dict
            return None
        except Exception as e:
            print(f"Error getting answer for user: {e}")
            return None

class ReportService:
    """Report related services"""
    
    @staticmethod
    def create_report(reporter_user_id, reported_answer_id, reason=None):
        """Create new report"""
        try:
            existing_report = db.session.query(Report).filter(
                Report.reporter_user_id == reporter_user_id,
                Report.reported_answer_id == reported_answer_id
            ).first()
            
            if existing_report:
                return False, "You have already reported this answer."
            
            answer = db.session.query(UserAnswer).filter(
                UserAnswer.id == reported_answer_id
            ).first()
            
            if not answer:
                return False, "Answer not found."
            
            if answer.user_id == reporter_user_id:
                return False, "You cannot report your own answer."
            
            new_report = Report.create(reporter_user_id, reported_answer_id, reason)
            db.session.add(new_report)
            db.session.commit()
            
            # Get the ID of the created report
            report_id = new_report.id
            
            return True, f"Report #{report_id} submitted successfully. Thank you for helping us maintain a safe community."
        except Exception as e:
            db.session.rollback()
            return False, f"Error creating report: {str(e)}"
