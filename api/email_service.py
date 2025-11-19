"""
Сервис для отправки email-уведомлений
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime


class EmailService:
    """Сервис для отправки email-уведомлений"""

    def __init__(self):
        """Инициализация email сервиса"""
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_user)
        self.from_name = os.getenv('FROM_NAME', 'Система викторин Aditi')

        # Проверка настроек
        if not self.smtp_user or not self.smtp_password:
            raise ValueError(
                "Email не настроен. Установите SMTP_USER и SMTP_PASSWORD в .env"
            )

    def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None
    ) -> bool:
        """
        Отправить email

        Args:
            to_email: Email получателя
            subject: Тема письма
            body_html: HTML содержимое письма
            body_text: Текстовая версия (опционально)

        Returns:
            True если успешно, False если ошибка
        """
        try:
            # Создаем сообщение
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject

            # Добавляем текстовую версию
            if body_text:
                part1 = MIMEText(body_text, 'plain', 'utf-8')
                msg.attach(part1)

            # Добавляем HTML версию
            part2 = MIMEText(body_html, 'html', 'utf-8')
            msg.attach(part2)

            # Отправляем
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            print(f"✅ Email отправлен: {to_email} - {subject}")
            return True

        except Exception as e:
            print(f"❌ Ошибка отправки email: {e}")
            return False

    def send_quiz_invitation(
        self,
        student_name: str,
        student_email: str,
        quiz_name: str,
        invitation_link: str,
        expires_at: Optional[str] = None,
        teacher_name: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        """
        Отправить приглашение на викторину

        Args:
            student_name: Имя студента
            student_email: Email студента
            quiz_name: Название викторины
            invitation_link: Ссылка на викторину
            expires_at: Срок действия приглашения
            teacher_name: Имя преподавателя
            notes: Дополнительные заметки

        Returns:
            True если успешно
        """
        subject = f"Приглашение на викторину: {quiz_name}"

        # HTML версия
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .container {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 30px;
                    border-radius: 10px;
                    color: white;
                }}
                .content {{
                    background: white;
                    padding: 30px;
                    border-radius: 8px;
                    color: #333;
                    margin-top: 20px;
                }}
                .button {{
                    display: inline-block;
                    padding: 15px 30px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-decoration: none;
                    border-radius: 8px;
                    margin: 20px 0;
                    font-weight: bold;
                }}
                .footer {{
                    margin-top: 20px;
                    font-size: 12px;
                    color: #666;
                    text-align: center;
                }}
                .warning {{
                    background: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 10px;
                    margin: 15px 0;
                    color: #856404;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1 style="margin: 0;">📝 Приглашение на викторину</h1>
            </div>

            <div class="content">
                <p>Здравствуйте, <strong>{student_name}</strong>!</p>

                <p>{teacher_name or 'Ваш преподаватель'} приглашает вас пройти викторину:</p>

                <h2 style="color: #667eea;">{quiz_name}</h2>

                {f'<div class="warning">⏰ <strong>Важно:</strong> Приглашение действительно до {expires_at}</div>' if expires_at else ''}

                {f'<p><strong>Заметка от преподавателя:</strong><br>{notes}</p>' if notes else ''}

                <p>Для прохождения викторины перейдите по ссылке:</p>

                <a href="{invitation_link}" class="button">🚀 Начать викторину</a>

                <div class="warning">
                    ⚠️ <strong>Внимание:</strong> Ссылка одноразовая и работает только для вас.
                    После начала викторины она станет недействительной.
                </div>

                <p>Удачи! 🍀</p>
            </div>

            <div class="footer">
                <p>Это автоматическое письмо от системы викторин Aditi</p>
                <p>Если у вас возникли вопросы, свяжитесь с преподавателем</p>
            </div>
        </body>
        </html>
        """

        # Текстовая версия
        text_body = f"""
Здравствуйте, {student_name}!

{teacher_name or 'Ваш преподаватель'} приглашает вас пройти викторину:

{quiz_name}

{'⏰ Важно: Приглашение действительно до ' + expires_at if expires_at else ''}

{f'Заметка от преподавателя: {notes}' if notes else ''}

Для прохождения викторины перейдите по ссылке:
{invitation_link}

⚠️ Внимание: Ссылка одноразовая и работает только для вас.

Удачи!

---
Это автоматическое письмо от системы викторин Aditi
        """

        return self.send_email(student_email, subject, html_body, text_body)

    def send_quiz_completion(
        self,
        student_name: str,
        student_email: str,
        quiz_name: str,
        score: float,
        max_score: float,
        percentage: float,
        ai_feedback: Optional[str] = None,
        teacher_notes: Optional[str] = None
    ) -> bool:
        """
        Отправить уведомление о завершении викторины

        Args:
            student_name: Имя студента
            student_email: Email студента
            quiz_name: Название викторины
            score: Набранные баллы
            max_score: Максимальные баллы
            percentage: Процент правильных ответов
            ai_feedback: AI-фидбэк
            teacher_notes: Заметки преподавателя

        Returns:
            True если успешно
        """
        subject = f"Результаты викторины: {quiz_name}"

        # Определяем эмодзи в зависимости от результата
        if percentage >= 90:
            emoji = "🎉"
            grade_text = "Отлично!"
        elif percentage >= 75:
            emoji = "👏"
            grade_text = "Хорошо!"
        elif percentage >= 60:
            emoji = "👍"
            grade_text = "Неплохо!"
        else:
            emoji = "📚"
            grade_text = "Требует улучшения"

        # HTML версия
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .container {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 30px;
                    border-radius: 10px;
                    color: white;
                }}
                .content {{
                    background: white;
                    padding: 30px;
                    border-radius: 8px;
                    color: #333;
                    margin-top: 20px;
                }}
                .score-box {{
                    background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
                    padding: 20px;
                    border-radius: 8px;
                    text-align: center;
                    margin: 20px 0;
                    border-left: 4px solid #667eea;
                }}
                .score-box h2 {{
                    font-size: 48px;
                    margin: 10px 0;
                    color: #667eea;
                }}
                .ai-section {{
                    background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                    border-left: 4px solid #667eea;
                }}
                .ai-badge {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 3px 10px;
                    border-radius: 12px;
                    font-size: 11px;
                    font-weight: bold;
                }}
                .teacher-notes {{
                    background: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 15px 0;
                    color: #856404;
                }}
                .footer {{
                    margin-top: 20px;
                    font-size: 12px;
                    color: #666;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1 style="margin: 0;">{emoji} Викторина завершена!</h1>
            </div>

            <div class="content">
                <p>Здравствуйте, <strong>{student_name}</strong>!</p>

                <p>Вы завершили викторину: <strong>{quiz_name}</strong></p>

                <div class="score-box">
                    <p style="margin: 0; color: #666; font-size: 14px;">{grade_text}</p>
                    <h2>{percentage:.1f}%</h2>
                    <p style="margin: 0; color: #666;">
                        <strong>{score:.1f}</strong> из <strong>{max_score:.1f}</strong> баллов
                    </p>
                </div>

                {f'''
                <div class="ai-section">
                    <h3 style="color: #667eea;">
                        🤖 AI-анализ
                        <span class="ai-badge">GEMINI</span>
                    </h3>
                    <p style="white-space: pre-wrap;">{ai_feedback}</p>
                </div>
                ''' if ai_feedback else ''}

                {f'''
                <div class="teacher-notes">
                    <h3 style="color: #856404; margin-top: 0;">📝 Заметки преподавателя</h3>
                    <p style="white-space: pre-wrap; margin-bottom: 0;">{teacher_notes}</p>
                </div>
                ''' if teacher_notes else ''}

                <p>Продолжайте в том же духе! 💪</p>
            </div>

            <div class="footer">
                <p>Это автоматическое письмо от системы викторин Aditi</p>
                <p>{datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
            </div>
        </body>
        </html>
        """

        # Текстовая версия
        text_body = f"""
{emoji} Викторина завершена!

Здравствуйте, {student_name}!

Вы завершили викторину: {quiz_name}

Результат: {grade_text}
Баллы: {score:.1f} из {max_score:.1f} ({percentage:.1f}%)

{f'🤖 AI-анализ (GEMINI):\\n{ai_feedback}\\n' if ai_feedback else ''}

{f'📝 Заметки преподавателя:\\n{teacher_notes}\\n' if teacher_notes else ''}

Продолжайте в том же духе!

---
Это автоматическое письмо от системы викторин Aditi
{datetime.now().strftime('%d.%m.%Y %H:%M')}
        """

        return self.send_email(student_email, subject, html_body, text_body)


# Пример использования
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    try:
        service = EmailService()

        # Тест отправки приглашения
        success = service.send_quiz_invitation(
            student_name="Иван Иванов",
            student_email="test@example.com",
            quiz_name="Викторина по математике",
            invitation_link="http://localhost:3000/quiz.html?token=abc123",
            expires_at="31.12.2025 23:59",
            teacher_name="Петров И.И.",
            notes="Пожалуйста, пройдите викторину до конца недели"
        )

        if success:
            print("✅ Тест прошел успешно!")
        else:
            print("❌ Тест не пройден")

    except ValueError as e:
        print(f"❌ {e}")
        print("\nДобавьте в .env:")
        print("SMTP_USER=your-email@gmail.com")
        print("SMTP_PASSWORD=your-app-password")
