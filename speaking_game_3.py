import pygame, threading
import speech_recognition as sr

# Инициализация Pygame
pygame.init()
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Говори Правильно")
clock = pygame.time.Clock()

# Цвета
WHITE, BLACK, BLUE, RED, GREEN = (255,255,255), (0,0,0), (0,0,255), (255,0,0), (0,128,0)
DARK_BLUE, GOLD, LIGHT_BLUE = (30,30,50), (255,215,0), (100,200,255)

# Шрифты
font_big = pygame.font.SysFont('Arial', 48, bold=True)
font_medium = pygame.font.SysFont('Arial', 28)

# Слова с картинками
words = [
    {"ru": "кот", "en": "cat", "img": "images/cat.jpg"},
    {"ru": "дом", "en": "house", "img": "images/house.jpg"},
    {"ru": "яблоко", "en": "apple", "img": "images/apple.jpg"},
    {"ru": "машина", "en": "car", "img": "images/car.jpg"},
    {"ru": "солнце", "en": "sun", "img": "images/sun.jpg"},
    {"ru": "вода", "en": "water", "img": "images/water.jpg"},
    {"ru": "книга", "en": "book", "img": "images/book.jpg"},
    {"ru": "стол", "en": "table", "img": "images/table.jpg"},
]

class SpeechGame:
    def __init__(self):
        self.current_word_index = 0
        self.recognition_result = ""
        self.is_listening = False
        self.show_translation = False
        self.correct_count = 0
        self.total_attempts = 0
        self.last_correct_word_index = -1
        self.frame_counter = 0
        self.show_hint = False
        self.hint_timer = 0
        self.game_completed = False
        self.running = True

    def draw_text_center(self, text, y, font, color=WHITE):
        rendered = font.render(text, True, color)
        x = WIDTH // 2 - rendered.get_width() // 2
        screen.blit(rendered, (x, y))

    def draw_progress_bar(self, current, total, y_pos=10):
        bar_width, bar_height = 600, 20
        x_pos = WIDTH // 2 - bar_width // 2
        pygame.draw.rect(screen, (50,50,70), (x_pos, y_pos, bar_width, bar_height))
        if total > 0:
            progress = current / total
            filled_width = int(bar_width * progress)
            pygame.draw.rect(screen, GREEN, (x_pos, y_pos, filled_width, bar_height))
        progress_text = f"{current}/{total}"
        text_surf = font_medium.render(progress_text, True, WHITE)
        screen.blit(text_surf, (x_pos + bar_width + 10, y_pos))

    def draw_recording_indicator(self):
        center_x, center_y = WIDTH // 2, 350
        radius = 20 + (self.frame_counter % 10)
        for r in range(radius, radius + 15, 3):
            alpha = 150 - (r - radius) * 10
            if alpha > 0:
                s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                pygame.draw.circle(s, (255,0,0,alpha), (r, r), r)
                screen.blit(s, (center_x - r, center_y - r))
        pygame.draw.circle(screen, RED, (center_x, center_y), 20)

    def recognize_speech(self):
        recognizer = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            text = recognizer.recognize_google(audio, language="ru-RU")
            return text.lower()
        except sr.WaitTimeoutError: return "timeout"
        except sr.UnknownValueError: return "unknown"
        except Exception: return "error"

    def speech_recognition_task(self):
        result = self.recognize_speech()
        self.is_listening = False
        self.recognition_result = result

    def start_listening(self):
        if not self.is_listening:
            self.is_listening = True
            self.recognition_result = "Слушаю..."
            self.show_translation = False
            self.show_hint = False
            thread = threading.Thread(target=self.speech_recognition_task)
            thread.daemon = True
            thread.start()
            self.total_attempts += 1

    def next_word(self):
        if self.current_word_index < len(words) - 1:
            self.current_word_index += 1
            self.reset_current_word_state()
        else: self.game_completed = True

    def previous_word(self):
        if self.current_word_index > 0:
            self.current_word_index -= 1
            self.reset_current_word_state()

    def reset_current_word_state(self):
        self.recognition_result = ""
        self.show_translation = False
        self.show_hint = False
        self.last_correct_word_index = -1

    def update_hint_timer(self):
        if self.hint_timer > 0: self.hint_timer -= 1
        else: self.show_hint = False

    def process_recognition_result(self):
        if not self.recognition_result or self.recognition_result == "Слушаю...": return
        current_word = words[self.current_word_index]
        if self.recognition_result == current_word["ru"]:
            if self.last_correct_word_index != self.current_word_index:
                self.correct_count += 1
                self.last_correct_word_index = self.current_word_index

    def get_recognition_display_text(self):
        if not self.recognition_result: return "", WHITE
        if self.recognition_result == "Слушаю...": return "Слушаю...", LIGHT_BLUE
        current_word = words[self.current_word_index]
        if self.recognition_result == current_word["ru"]:
            return f"Вы сказали: {self.recognition_result}", GREEN
        error_messages = {"timeout": "Время ожидания истекло", "unknown": "Речь не распознана", "error": "Ошибка распознавания"}
        display_text = error_messages.get(self.recognition_result, f"Вы сказали: {self.recognition_result}")
        return display_text, RED

    def draw_game_screen(self):
        screen.fill(DARK_BLUE)
        current_word = words[self.current_word_index]
        
        # Прогресс-бар
        self.draw_progress_bar(self.current_word_index + 1, len(words))
        
        # Изображение
        try:
            img = pygame.image.load(current_word["img"])
            img = pygame.transform.scale(img, (400, 300))
            screen.blit(img, (WIDTH//2 - 200, HEIGHT//2 - 150))
        except: pass
        
        # Текущее слово
        self.draw_text_center(f"Слово: {current_word['ru']}", 50, font_big, BLUE)
        
        # Результат распознавания
        display_text, color = self.get_recognition_display_text()
        if display_text: self.draw_text_center(display_text, 380, font_medium, color)
        
        # Перевод
        if self.show_translation:
            self.draw_text_center(f"Перевод: {current_word['en']}", 420, font_medium, GOLD)
        
        # Подсказка
        if self.show_hint:
            self.draw_text_center(f"Подсказка: {current_word['ru'][0]}...", 450, font_medium, LIGHT_BLUE)
        
        # Статистика
        if self.total_attempts > 0:
            accuracy = int((self.correct_count / self.total_attempts) * 100)
            self.draw_text_center(f"Правильно: {self.correct_count}/{self.total_attempts} ({accuracy}%)", 480, font_medium, LIGHT_BLUE)
        
        # Инструкции
        self.draw_text_center("ПРОБЕЛ - говорить, ENTER - следующее слово", 520, font_medium, WHITE)
        self.draw_text_center("←/→ - навигация, T - перевод, H - подсказка, R - сброс", 550, font_medium, WHITE)
        
        # Индикатор записи
        if self.is_listening:
            self.draw_recording_indicator()
            self.draw_text_center("Запись... ГОВОРИТЕ СЕЙЧАС", 320, font_medium, RED)

    def show_final_screen(self):
        screen.fill(DARK_BLUE)
        self.draw_text_center("Игра окончена!", HEIGHT//2 - 80, font_big, BLUE)
        if self.total_attempts > 0:
            accuracy = int((self.correct_count / self.total_attempts) * 100)
            self.draw_text_center(f"Итоговый результат: {self.correct_count}/{self.total_attempts}", HEIGHT//2 - 20, font_medium, GREEN)
            self.draw_text_center(f"Точность: {accuracy}%", HEIGHT//2 + 20, font_medium, GOLD)
        self.draw_text_center("Нажми любую клавишу для выхода", HEIGHT//2 + 120, font_medium, WHITE)
        pygame.display.flip()
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type in (pygame.QUIT, pygame.KEYDOWN): waiting = False

    def run(self):
        while self.running:
            self.frame_counter += 1
            if self.game_completed:
                self.show_final_screen()
                break
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and not self.game_completed: self.start_listening()
                    elif event.key == pygame.K_RETURN and not self.game_completed: self.next_word()
                    elif event.key == pygame.K_t and not self.game_completed: self.show_translation = not self.show_translation
                    elif event.key == pygame.K_h and not self.game_completed: self.show_hint = True
                    elif event.key == pygame.K_r and not self.game_completed: self.reset_current_word_state()
                    elif event.key == pygame.K_LEFT and not self.game_completed: self.previous_word()
                    elif event.key == pygame.K_RIGHT and not self.game_completed: self.next_word()
                    elif event.key == pygame.K_ESCAPE: self.running = False
            
            self.update_hint_timer()
            self.process_recognition_result()
            self.draw_game_screen()
            pygame.display.flip()
            clock.tick(60)

if __name__ == "__main__":
    game = SpeechGame()
    game.run()
    pygame.quit()