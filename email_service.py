import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import os
from dotenv import load_dotenv

load_dotenv()


class EmailService:
    """Email sending service"""
    
    def __init__(self):
        self.from_email = os.getenv("FROM_EMAIL")
        self.bcc_email = os.getenv("BCC_EMAIL")
        self.password = os.getenv("PASSWORD")
        self.app_url = os.getenv("APP_URL", "https://yourapp.com")
    
    def send_welcome_email(self, user_data):
        """Send welcome email"""
        try:
            subject = "[Mindscape] Welcome to your self-reflection journey!"
            html_body = self._create_welcome_html(user_data["username"])
            text_body = self._create_welcome_text(user_data["username"])
            
            self._send_html_email(user_data["email"], subject, html_body, text_body)
            return True, "Welcome email sent successfully."
        except Exception as e:
            return False, f"Failed to send welcome email: {str(e)}"
    
    def send_password_reset_email(self, user_data, temp_password):
        """Send password reset email"""
        try:
            subject = "[Mindscape] Password Reset - Temporary Login Credentials"
            html_body = self._create_password_reset_html(user_data["username"], temp_password)
            text_body = self._create_password_reset_text(user_data["username"], temp_password)
            
            self._send_html_email(user_data["email"], subject, html_body, text_body)
            return True, "Password reset email sent successfully."
        except Exception as e:
            return False, f"Failed to send password reset email: {str(e)}"
    
    def send_inquiry_email(self, inquiry_data):
        """Send inquiry confirmation email"""
        try:
            subject = "[Mindscape] Message received - We'll get back to you soon!"
            html_body = self._create_inquiry_html(inquiry_data)
            text_body = self._create_inquiry_text(inquiry_data)
            
            self._send_html_email(inquiry_data["email"], subject, html_body, text_body)
            return True, "Your message was submitted successfully."
        except Exception as e:
            return False, f"Failed to send email: {str(e)}"
    
    def send_report_notification_email(self, report_data):
        """Send report notification email to admins and reporter"""
        try:
            # Send to admin
            admin_subject = "[Mindscape] New Report Submitted"
            admin_html_body = self._create_admin_report_html(report_data)
            admin_text_body = self._create_admin_report_text(report_data)
            
            # Send to admin (BCC email)
            if self.bcc_email:
                self._send_html_email(self.bcc_email, admin_subject, admin_html_body, admin_text_body)
            
            # Send confirmation to reporter
            reporter_subject = "[Mindscape] Report Submitted Successfully"
            reporter_html_body = self._create_reporter_confirmation_html(report_data)
            reporter_text_body = self._create_reporter_confirmation_text(report_data)
            
            self._send_html_email(report_data["reporter_email"], reporter_subject, reporter_html_body, reporter_text_body)
            
            return True, "Report notification emails sent successfully."
        except Exception as e:
            return False, f"Failed to send report notification emails: {str(e)}"
    
    def _create_welcome_html(self, username):
        """Create welcome email HTML"""
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h1 style="color: #000; border-bottom: 2px solid #000; padding-bottom: 10px;">Welcome to Mindscape!</h1>
                    <p>Hi {username},</p>
                    <p>Thank you for joining our community of self-reflection! Your account has been successfully created.</p>
                    <div style="background-color: #f8f9fa; padding: 20px; border-left: 4px solid #000; margin: 20px 0;">
                        <h3 style="margin-top: 0;">What's next?</h3>
                        <ul>
                            <li>Start answering daily questions to discover more about yourself</li>
                            <li>Build a personal journal of your thoughts and growth</li>
                            <li>Filter and review your previous answers anytime</li>
                            <li>Share your insights with the community or keep them private</li>
                            <li>Download your data whenever you need it</li>
                        </ul>
                    </div>
                    <p>Ready to begin your journey? <a href="{self.app_url}" style="color: #000; text-decoration: none; font-weight: bold;">Start answering questions</a></p>
                    <p>If you have any questions, don't hesitate to contact us through our platform.</p>
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                    <p style="color: #666; font-size: 0.9em;">
                        This email was sent because you created an account at Mindscape.<br>
                        If you didn't create this account, please contact us immediately.
                    </p>
                </div>
            </body>
        </html>
        """
    
    def _create_welcome_text(self, username):
        """Create welcome email text"""
        return f"""Hi {username},

Thank you for joining our community of self-reflection! Your account has been successfully created.

What's next?
- Start answering daily questions to discover more about yourself
- Build a personal journal of your thoughts and growth
- Filter and review your previous answers anytime
- Share your insights with the community or keep them private
- Download your data whenever you need it

Ready to begin your journey? Visit: {self.app_url}

---
Mindscape Team
"""
    
    def _create_password_reset_html(self, username, temp_password):
        """Create password reset email HTML"""
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h1 style="color: #000; border-bottom: 2px solid #000; padding-bottom: 10px;">Password Reset Request</h1>
                    <p>Hi {username},</p>
                    <p>We received a request to reset your password for your Mindscape account.</p>
                    <div style="background-color: #fff3cd; padding: 20px; border-left: 4px solid #ffc107; margin: 20px 0;">
                        <h3 style="margin-top: 0; color: #856404;">Temporary Password</h3>
                        <p style="margin-bottom: 0; font-family: monospace; font-size: 1.2em; background-color: #fff; padding: 10px; border: 1px solid #ddd;">
                            <strong>{temp_password}</strong>
                        </p>
                    </div>
                    <div style="background-color: #f8d7da; padding: 20px; border-left: 4px solid #dc3545; margin: 20px 0;">
                        <h3 style="margin-top: 0; color: #721c24;">Important Security Information</h3>
                        <ul style="margin-bottom: 0;">
                            <li>This temporary password expires in 24 hours</li>
                            <li>You will be prompted to change it immediately after logging in</li>
                            <li>For security, please don't share this password with anyone</li>
                            <li>If you didn't request this reset, contact us immediately</li>
                        </ul>
                    </div>
                    <p><a href="{self.app_url}/login" style="display: inline-block; background-color: #000; color: #fff; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold;">Login Now</a></p>
                </div>
            </body>
        </html>
        """
    
    def _create_password_reset_text(self, username, temp_password):
        """Create password reset email text"""
        return f"""Hi {username},

We received a request to reset your password for your Mindscape account.

TEMPORARY PASSWORD: {temp_password}

Important Security Information:
- This temporary password expires in 24 hours
- You will be prompted to change it immediately after logging in
- For security, please don't share this password with anyone
- If you didn't request this reset, contact us immediately

Login here: {self.app_url}/login

---
Mindscape Team
"""
    
    def _create_inquiry_html(self, inquiry_data):
        """Create inquiry confirmation email HTML"""
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h1 style="color: #000; border-bottom: 2px solid #000; padding-bottom: 10px;">Thank you for contacting us!</h1>
                    <p>Hi {inquiry_data["name"]},</p>
                    <p>Thank you for reaching out to us! We've received your message and will get back to you as soon as possible.</p>
                    <div style="background-color: #f8f9fa; padding: 20px; border-left: 4px solid #000; margin: 20px 0;">
                        <h3 style="margin-top: 0;">Your Message Details</h3>
                        <p><strong>Email:</strong> {inquiry_data["email"]}</p>
                        <p><strong>Category:</strong> {inquiry_data["category"]}</p>
                        <p><strong>Message:</strong></p>
                        <div style="background-color: #fff; padding: 15px; border: 1px solid #ddd; border-radius: 4px;">
                            {inquiry_data["message"].replace(chr(10), '<br>')}
                        </div>
                    </div>
                    <p>We typically respond within 24-48 hours during business days. Thank you for your patience!</p>
                </div>
            </body>
        </html>
        """
    
    def _create_inquiry_text(self, inquiry_data):
        """Create inquiry confirmation email text"""
        return f"""Hi {inquiry_data["name"]},

Thank you for reaching out to us! We've received your message and will get back to you as soon as possible.

Your Message Details:
Email: {inquiry_data["email"]}
Category: {inquiry_data["category"]}
Message: {inquiry_data["message"]}

We typically respond within 24-48 hours during business days. Thank you for your patience!

---
Mindscape Team
"""
    
    def _create_admin_report_html(self, report_data):
        """Create admin report notification email HTML"""
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h1 style="color: #dc3545; border-bottom: 2px solid #dc3545; padding-bottom: 10px;">New Report Submitted</h1>
                    <div style="background-color: #f8d7da; padding: 20px; border-left: 4px solid #dc3545; margin: 20px 0;">
                        <h3 style="margin-top: 0; color: #721c24;">Report Details</h3>
                        <p><strong>Report ID:</strong> #{report_data["report_id"]}</p>
                        <p><strong>Reporter:</strong> {report_data["reporter_username"]} ({report_data["reporter_email"]})</p>
                        <p><strong>Reported Answer ID:</strong> {report_data["reported_answer_id"]}</p>
                        <p><strong>Reason:</strong> {report_data["reason"]}</p>
                        <p><strong>Submitted:</strong> {report_data["created_at"]}</p>
                    </div>
                    <div style="background-color: #f8f9fa; padding: 20px; border-left: 4px solid #000; margin: 20px 0;">
                        <h3 style="margin-top: 0;">Reported Content</h3>
                        <p><strong>Question:</strong> {report_data["question"]}</p>
                        <p><strong>Answer:</strong> {report_data["answer"]}</p>
                        <p><strong>By:</strong> {report_data["reported_username"]}</p>
                    </div>
                    <p>Please review this report and take appropriate action if necessary.</p>
                    <p><strong>Action Required:</strong> Check the reported content and determine if it violates community guidelines.</p>
                </div>
            </body>
        </html>
        """
    
    def _create_admin_report_text(self, report_data):
        """Create admin report notification email text"""
        return f"""New Report Submitted - Report #{report_data["report_id"]}

Report Details:
Reporter: {report_data["reporter_username"]} ({report_data["reporter_email"]})
Reported Answer ID: {report_data["reported_answer_id"]}
Reason: {report_data["reason"]}
Submitted: {report_data["created_at"]}

Reported Content:
Question: {report_data["question"]}
Answer: {report_data["answer"]}
By: {report_data["reported_username"]}

Please review this report and take appropriate action if necessary.

---
Mindscape Admin System
"""

    def _create_reporter_confirmation_html(self, report_data):
        """Create reporter confirmation email HTML"""
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h1 style="color: #000; border-bottom: 2px solid #000; padding-bottom: 10px;">Thank You for Your Report</h1>
                    <p>Hi {report_data["reporter_username"]},</p>
                    <p>Thank you for helping us maintain a safe and respectful community. Your opinion is valuable to us, and we truly appreciate you taking the time to report this content.</p>
                    <div style="background-color: #d4edda; padding: 20px; border-left: 4px solid #28a745; margin: 20px 0;">
                        <h3 style="margin-top: 0; color: #155724;">What happens next?</h3>
                        <ul>
                            <li>Our moderation team will carefully review the reported content</li>
                            <li>We'll take appropriate action if the content violates our community guidelines</li>
                            <li>We typically complete reviews within 24-48 hours</li>
                            <li>Your report helps make Mindscape a better place for everyone</li>
                        </ul>
                    </div>
                    <p>Thanks again for your valuable contribution. We hope you continue to enjoy organizing your thoughts and growing through self-reflection on Mindscape!</p>
                    <p>Best regards,<br>The Mindscape Team</p>
                </div>
            </body>
        </html>
        """

    def _create_reporter_confirmation_text(self, report_data):
        """Create reporter confirmation email text"""
        return f"""Hi {report_data["reporter_username"]},

Thank you for helping us maintain a safe and respectful community. Your opinion is valuable to us, and we truly appreciate you taking the time to report this content.

What happens next?
- Our moderation team will carefully review the reported content
- We'll take appropriate action if the content violates our community guidelines
- We typically complete reviews within 24-48 hours
- Your report helps make Mindscape a better place for everyone

Thanks again for your valuable contribution. We hope you continue to enjoy organizing your thoughts and growing through self-reflection on Mindscape!

Best regards,
The Mindscape Team
"""

    def _send_html_email(self, to_email, subject, html_body, text_body):
        """Send HTML email"""
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as connection:
                connection.login(user=self.from_email, password=self.password)
                
                msg = MIMEMultipart('alternative')
                msg['Subject'] = Header(subject.encode('utf-8'), 'utf-8')
                msg['From'] = self.from_email
                msg['To'] = to_email
                
                # Build BCC list including sender email and configured BCC email
                bcc_list = []
                # Always add sender email to BCC
                if self.from_email and self.from_email != to_email:
                    bcc_list.append(self.from_email)
                # Add configured BCC email if different from sender and recipient
                if self.bcc_email and self.bcc_email != to_email and self.bcc_email != self.from_email:
                    bcc_list.append(self.bcc_email)
                
                if bcc_list:
                    msg['Bcc'] = ', '.join(bcc_list)
                
                part1 = MIMEText(text_body.encode('utf-8'), 'plain', 'utf-8')
                part2 = MIMEText(html_body.encode('utf-8'), 'html', 'utf-8')
                
                msg.attach(part1)
                msg.attach(part2)
                
                # Determine recipients for actual sending (to + all BCCs)
                recipients = [to_email]
                if bcc_list:
                    recipients.extend(bcc_list)
                
                connection.sendmail(self.from_email, recipients, msg.as_string())
                
        except Exception as e:
            raise e
