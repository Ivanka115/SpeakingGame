import pygame
import sys
import os
import requests
from PIL import Image, ImageDraw, ImageFont
import io
import json
import speech_recognition as sr
import sounddevice as sd
from scipy.io.wavfile import write
import tempfile
import random
import time
import numpy as np
import wave

# Инициализация Pygame
pygame.init()

# Настройки окна
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Говори Правильно - Игра с Переводом")

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 128, 0)
DARK_BLUE = (30, 30, 50)
GOLD = (255, 215, 0)
LIGHT_BLUE = (100, 200, 255)

# Шрифты
font = pygame.font.SysFont('Arial', 24)
title_font = pygame.font.SysFont('Arial', 32, bold=True)
large_font = pygame.font.SysFont('Arial', 48, bold=True)

class SpeakingGame:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.score = 0
        self.lives = 3
        self.streak = 0
        self.max_streak = 0
        self.session_stats = {
            "games_played": 0,
            "total_score": 0,
            "best_score": 0,
            "words_learned": set()
        }
        
        # Загрузка статистики
        self.load_stats()
        
        self.levels = {
            "1": {"name": "Новичок", "words": 5, "time_limit": 10, "multiplier": 1},
            "2": {"name": "Средний", "words": 8, "time_limit": 8, "multiplier": 1.5},
            "3": {"name": "Эксперт", "words": 12, "time_limit": 5, "multiplier": 2}
        }
        
        # Тематические наборы слов с изображениями
        self.word_categories = {
            "1": {"name": "Базовые слова", "words": {
                "кот": "cat", "собака": "dog", "дом": "house", "солнце": "sun",
                "вода": "water", "книга": "book", "стол": "table", "окно": "window",
                "яблоко": "apple", "машина": "car", "рука": "hand", "нога": "leg"
            }, "images":{
                "кот": "cat.jpg",
                "собака": "dog.webp",
                "дом": "house.jpg",
                "солнце": "sun.jpg",
                "вода": "water.jpg", 
                "книга": "book.jpg", 
                "стол": "table.jpg", 
                "окно": "window.jpg",
                "яблоко": "apple.jpg", 
                "машина": "car.jpg", 
                "рука": "hand.jpg", 
                "нога": "leg.jpg"
            }},
            "2": {"name": "Еда и напитки", "words": {
                "хлеб": "bread", "молоко": "milk", "чай": "tea", "кофе": "coffee",
                "суп": "soup", "сыр": "cheese", "мясо": "meat", "рыба": "fish",
                "фрукты": "fruits", "овощи": "vegetables", "салат": "salad"
            }, "images":{
                "хлеб": "bread.jpg", 
                "молоко": "milk.jpg", 
                "чай": "tea.jpg", 
                "кофе": "coffee.jpg",
                "суп": "soup.jpg", 
                "сыр": "cheese.jpg", 
                "мясо": "meat.jpg", 
                "рыба": "fish.jpg",
                "фрукты": "fruits.jpg", 
                "овощи": "vegetables.jpg", 
                "салат": "salad.jpg"
            }},
            "3": {"name": "Природа и животные", "words": {
                "дерево": "tree", "цветок": "flower", "птица": "bird", "лес": "forest",
                "река": "river", "море": "sea", "горы": "mountains", "небо": "sky",
                "звезда": "star", "луна": "moon", "погода": "weather"
            }, "images":{
                "дерево": "tree.jpg", 
                "цветок": "flower.jpg", 
                "птица": "bird.jpg", 
                "лес": "forest.jpg",
                "река": "river.jpg", 
                "море": "sea.jpg", 
                "горы": "mountains.jpg", 
                "небо": "sky.jpg",
                "звезда": "star.jpg", 
                "луна": "moon.jpg", 
                "погода": "weather.jpg"
            }},
            "4": {"name": "Город и транспорт", "words": {
                "город": "city", "улица": "street", "парк": "park", "магазин": "shop",
                "школа": "school", "больница": "hospital", "автобус": "bus",
                "поезд": "train", "самолет": "airplane", "велосипед": "bicycle"
            }, "images": {
                "город": "city.jpg", 
                "улица": "street.jpg", 
                "парк": "park.jpg", 
                "магазин": "shop.jpg",
                "школа": "school.jpg", 
                "больница": "hospital.jpg", 
                "автобус": "bus.jpg",
                "поезд": "train.jpg", 
                "самолет": "airplane.jpg", 
                "велосипед": "bicycle.jpg"
            }}
        }
        
        # Система достижений
        self.achievements = {
            "first_blood": {"name": "Первая кровь", "desc": "Завершите первую игру", "earned": False},
            "streak_master": {"name": "Мастер серии", "desc": "Достигните серии из 5 правильных ответов", "earned": False},
            "perfectionist": {"name": "Перфекционист", "desc": "Пройдите уровень без ошибок", "earned": False},
            "vocabulary": {"name": "Словарный запас", "desc": "Выучите 20 слов", "earned": False},
            "speed_demon": {"name": "Скоростной демон", "desc": "Пройдите экспертный уровень", "earned": False},
            "visual_learner": {"name": "Визуал", "desc": "Попробуйте режим с картинками", "earned": False}
        }
        
        # Текущее состояние игры
        self.current_state = "menu"
        self.current_word_index = 0
        self.current_words = []
        self.current_category = None
        self.current_level = None
        self.game_mode = None
        self.recording = False
        self.recording_start_time = 0
        self.recording_duration = 0
        self.last_result = None
        self.waiting_for_input = False
        self.current_image = None

    def create_unified_translation_image(self, russian_word, english_translation, category_id):
        """Создает единое изображение с русским и английским текстом"""
        try:
            # Параметры изображения
            width, height = 800, 600
            image = Image.new('RGB', (width, height), color=(30, 30, 50))
            draw = ImageDraw.Draw(image)
            
            # Загрузка шрифтов
            try:
                title_font = ImageFont.truetype("arial.ttf", 48)
                subtitle_font = ImageFont.truetype("arial.ttf", 36)
                info_font = ImageFont.truetype("arial.ttf", 20)
            except:
                title_font = ImageFont.load_default()
                subtitle_font = ImageFont.load_default()
                info_font = ImageFont.load_default()
            
            # Заголовок
            title_text = "🎓 ОБУЧЕНИЕ АНГЛИЙСКОМУ"
            title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (width - title_width) // 2
            draw.text((title_x, 30), title_text, fill=(255, 215, 0), font=title_font)
            
            # Разделительная линия
            draw.line([(50, 100), (width-50, 100)], fill=(100, 100, 150), width=2)
            
            # Русское слово (крупно)
            russian_bbox = draw.textbbox((0, 0), russian_word.upper(), font=title_font)
            russian_width = russian_bbox[2] - russian_bbox[0]
            russian_x = (width - russian_width) // 2
            draw.text((russian_x, 150), russian_word.upper(), fill=(255, 255, 255), font=title_font)
            
            # Метка "Русский"
            draw.text((width//2 - 100, 220), "РУССКИЙ", fill=(100, 200, 100), font=info_font)
            
            # Стрелка перевода
            arrow_y = 280
            draw.polygon([(width//2-20, arrow_y), (width//2+20, arrow_y), (width//2, arrow_y+40)], fill=(100, 200, 255))
            draw.text((width//2-30, arrow_y+50), "ПЕРЕВОД", fill=(100, 200, 255), font=info_font)
            
            # Английский перевод (крупно)
            english_bbox = draw.textbbox((0, 0), english_translation.upper(), font=title_font)
            english_width = english_bbox[2] - english_bbox[0]
            english_x = (width - english_width) // 2
            draw.text((english_x, 350), english_translation.upper(), fill=(100, 200, 255), font=title_font)
            
            # Метка "Английский"
            draw.text((width//2 - 100, 420), "АНГЛИЙСКИЙ", fill=(100, 200, 255), font=info_font)
            
            # Инструкция для пользователя
            instruction = "🎤 Произнесите английское слово вслух после сигнала!"
            instr_bbox = draw.textbbox((0, 0), instruction, font=info_font)
            instr_width = instr_bbox[2] - instr_bbox[0]
            instr_x = (width - instr_width) // 2
            draw.text((instr_x, 500), instruction, fill=(255, 150, 100), font=info_font)
            
            # Рамка вокруг всего изображения
            draw.rectangle([10, 10, width-10, height-10], outline=(100, 100, 150), width=3)
            
            # Сохранение изображения
            filename = f"translation_{russian_word}.jpg"
            image.save(filename)
            
            # Загрузка изображения в Pygame
            pygame_image = pygame.image.load(filename)
            return pygame_image
            
        except Exception as e:
            print(f"⚠️ Ошибка создания изображения: {e}")
            return None

    def load_stats(self):
        """Загрузка статистики из файла"""
        try:
            with open("game_stats.json", "r", encoding="utf-8") as f:
                self.session_stats = json.load(f)
                self.session_stats["words_learned"] = set(self.session_stats.get("words_learned", []))
        except FileNotFoundError:
            pass

    def save_stats(self):
        """Сохранение статистики в файл"""
        try:
            stats_to_save = self.session_stats.copy()
            stats_to_save["words_learned"] = list(stats_to_save["words_learned"])
            with open("game_stats.json", "w", encoding="utf-8") as f:
                json.dump(stats_to_save, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Не удалось сохранить статистику: {e}")

    def record_audio(self, duration=5, sample_rate=44100):
        """Запись аудио с микрофона"""
        print("\n🎤 Запись начинается... Говорите!")
        try:
            audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
            sd.wait()
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                write(tmp_file.name, sample_rate, audio_data)
                return tmp_file.name
        except Exception as e:
            print(f"❌ Ошибка записи аудио: {e}")
            return None

    def recognize_speech(self, audio_file):
        """Распознавание речи из аудиофайла"""
        if not audio_file:
            return None
            
        try:
            with sr.AudioFile(audio_file) as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio, language='en-US')
                return text.lower()
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            print(f"❌ Ошибка сервиса распознавания: {e}")
            return None

    def get_word_list(self, category_id, level):
        """Получение списка слов в зависимости от категории и уровня"""
        category = self.word_categories[category_id]
        all_words = list(category["words"].keys())
        return random.sample(all_words, self.levels[level]["words"])

    def analyze_pronunciation(self, audio_file, correct_word):
        """Анализ произношения"""
        try:
            with wave.open(audio_file, 'rb') as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                duration = frames / float(rate)
                
                signal = wav_file.readframes(frames)
                audio_data = np.frombuffer(signal, dtype=np.int16)
                volume = np.sqrt(np.mean(audio_data**2))
                
                feedback = []
                
                if duration < 0.5:
                    feedback.append("🗣️ Слишком коротко")
                elif duration > 3.0:
                    feedback.append("🗣️ Слишком долго")
                else:
                    feedback.append("🗣️ Хорошая длительность")
                
                if volume < 1000:
                    feedback.append("🔈 Слишком тихо")
                elif volume > 10000:
                    feedback.append("🔊 Слишком громко")
                else:
                    feedback.append("🔊 Хорошая громкость")
                
                return feedback
        except:
            return ["🔧 Анализ произношения недоступен"]

    def check_achievements(self):
        """Проверка и выдача достижений"""
        new_achievements = []
        
        if not self.achievements["first_blood"]["earned"] and self.session_stats["games_played"] > 0:
            self.achievements["first_blood"]["earned"] = True
            new_achievements.append("first_blood")
        
        if not self.achievements["streak_master"]["earned"] and self.streak >= 5:
            self.achievements["streak_master"]["earned"] = True
            new_achievements.append("streak_master")
        
        if not self.achievements["vocabulary"]["earned"] and len(self.session_stats["words_learned"]) >= 20:
            self.achievements["vocabulary"]["earned"] = True
            new_achievements.append("vocabulary")
        
        return new_achievements

    def start_game(self, category_id, level_id, game_mode):
        """Начало новой игры"""
        self.current_category = category_id
        self.current_level = level_id
        self.game_mode = game_mode
        self.current_words = self.get_word_list(category_id, level_id)
        self.current_word_index = 0
        self.score = 0
        self.streak = 0
        self.lives = 3 if game_mode == "1" else 999
        self.current_state = "game"
        self.session_stats["games_played"] += 1
        
        # Создаем первое изображение для визуального режима
        if game_mode == "3" and self.current_words:
            first_word = self.current_words[0]
            english_translation = self.word_categories[category_id]["words"][first_word]
            self.current_image = self.create_unified_translation_image(first_word, english_translation, category_id)

    def draw_menu(self):
        """Отрисовка главного меню"""
        screen.fill(DARK_BLUE)
        
        # Заголовок
        title = title_font.render("🎓 ГОВОРИ ПРАВИЛЬНО", True, GOLD)
        subtitle = font.render("Учи английский с помощью речи", True, LIGHT_BLUE)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))
        screen.blit(subtitle, (WIDTH//2 - subtitle.get_width()//2, 100))
        
        # Статистика
        stats_y = 150
        stats_text = [
            f"🎮 Игр сыграно: {self.session_stats['games_played']}",
            f"🏆 Лучший счет: {self.session_stats['best_score']}",
            f"📚 Слов выучено: {len(self.session_stats['words_learned'])}"
        ]
        
        for text in stats_text:
            stat_surface = font.render(text, True, WHITE)
            screen.blit(stat_surface, (WIDTH//2 - stat_surface.get_width()//2, stats_y))
            stats_y += 40
        
        # Выбор категории
        cat_y = 300
        cat_title = font.render("📚 ВЫБЕРИТЕ КАТЕГОРИЮ СЛОВ:", True, WHITE)
        screen.blit(cat_title, (WIDTH//2 - cat_title.get_width()//2, cat_y))
        cat_y += 40
        
        for key, category in self.word_categories.items():
            image_info = f" 🖼️({len(category.get('images', {}))} изображений)"
            cat_text = font.render(f"{key}. {category['name']} ({len(category['words'])} слов){image_info}", True, LIGHT_BLUE)
            screen.blit(cat_text, (WIDTH//2 - cat_text.get_width()//2, cat_y))
            cat_y += 30
        
        # Выбор уровня
        level_y = 450
        level_title = font.render("🎚️ ВЫБЕРИТЕ УРОВЕНЬ СЛОЖНОСТИ:", True, WHITE)
        screen.blit(level_title, (WIDTH//2 - level_title.get_width()//2, level_y))
        level_y += 40
        
        for key, level in self.levels.items():
            level_text = font.render(f"{key}. {level['name']} ({level['words']} слов, {level['time_limit']} сек)", True, LIGHT_BLUE)
            screen.blit(level_text, (WIDTH//2 - level_text.get_width()//2, level_y))
            level_y += 30
        
        # Выбор режима
        mode_y = 550
        mode_title = font.render("🎮 ВЫБЕРИТЕ РЕЖИМ ИГРЫ:", True, WHITE)
        screen.blit(mode_title, (WIDTH//2 - mode_title.get_width()//2, mode_y))
        mode_y += 40
        
        modes = [
            "1. 🎯 Классический режим (с жизнями)",
            "2. 🏋️ Тренировочный режим (без жизней)",
            "3. 🖼️ Визуальный режим (с переводом изображений)"
        ]
        
        for mode in modes:
            mode_surface = font.render(mode, True, LIGHT_BLUE)
            screen.blit(mode_surface, (WIDTH//2 - mode_surface.get_width()//2, mode_y))
            mode_y += 30
        
        # Инструкция
        instruction = font.render("Нажмите цифру для выбора, ESC для выхода", True, WHITE)
        screen.blit(instruction, (WIDTH//2 - instruction.get_width()//2, HEIGHT - 50))

    def draw_game(self):
        """Отрисовка игрового экрана"""
        screen.fill(DARK_BLUE)
        
        # Прогресс
        progress = int((self.current_word_index / len(self.current_words)) * 20)
        bar = "█" * progress + "░" * (20 - progress)
        progress_text = font.render(f"📊 Прогресс: [{bar}] {self.current_word_index}/{len(self.current_words)}", True, WHITE)
        screen.blit(progress_text, (20, 20))
        
        # Статистика
        stats_text = font.render(f"🎯 Счет: {self.score} | ❤️ Жизни: {self.lives} | 🔥 Серия: {self.streak}", True, WHITE)
        screen.blit(stats_text, (WIDTH - stats_text.get_width() - 20, 20))
        
        # Текущее слово
        current_word_ru = self.current_words[self.current_word_index]
        current_category = self.word_categories[self.current_category]
        correct_answer = current_category["words"][current_word_ru]
        
        # Визуальный режим - показываем изображение
        if self.game_mode == "3" and self.current_image:
            # Масштабируем изображение для отображения
            scaled_image = pygame.transform.scale(self.current_image, (600, 450))
            screen.blit(scaled_image, (WIDTH//2 - 300, HEIGHT//2 - 225))
        else:
            # Классический режим - показываем текст
            # Отображение русского слова
            ru_text = large_font.render(current_word_ru.upper(), True, WHITE)
            screen.blit(ru_text, (WIDTH//2 - ru_text.get_width()//2, HEIGHT//2 - 100))
            
            ru_label = font.render("РУССКИЙ", True, GREEN)
            screen.blit(ru_label, (WIDTH//2 - ru_label.get_width()//2, HEIGHT//2 - 150))
            
            # Стрелка перевода
            pygame.draw.polygon(screen, LIGHT_BLUE, [
                (WIDTH//2 - 20, HEIGHT//2 - 30),
                (WIDTH//2 + 20, HEIGHT//2 - 30),
                (WIDTH//2, HEIGHT//2 + 10)
            ])
            
            translate_label = font.render("ПЕРЕВОД", True, LIGHT_BLUE)
            screen.blit(translate_label, (WIDTH//2 - translate_label.get_width()//2, HEIGHT//2 + 20))
            
            # Английский перевод
            en_text = large_font.render(correct_answer.upper(), True, LIGHT_BLUE)
            screen.blit(en_text, (WIDTH//2 - en_text.get_width()//2, HEIGHT//2 + 80))
            
            en_label = font.render("АНГЛИЙСКИЙ", True, LIGHT_BLUE)
            screen.blit(en_label, (WIDTH//2 - en_label.get_width()//2, HEIGHT//2 + 150))
        
        # Инструкция
        if self.recording:
            elapsed = time.time() - self.recording_start_time
            remaining = max(0, self.recording_duration - elapsed)
            instruction = font.render(f"🎤 Запись... Говорите! Осталось: {remaining:.1f} сек", True, RED)
        else:
            instruction = font.render("🎤 Нажмите ПРОБЕЛ для начала записи", True, GOLD)
        
        screen.blit(instruction, (WIDTH//2 - instruction.get_width()//2, HEIGHT - 100))
        
        # Результат предыдущей попытки
        if self.last_result:
            result_color = GREEN if self.last_result["correct"] else RED
            result_text = font.render(self.last_result["message"], True, result_color)
            screen.blit(result_text, (WIDTH//2 - result_text.get_width()//2, HEIGHT - 150))

    def draw_result(self):
        """Отрисовка экрана результатов"""
        screen.fill(DARK_BLUE)
        
        # Заголовок
        title = title_font.render("🎊 РЕЗУЛЬТАТЫ ИГРЫ", True, GOLD)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))
        
        # Статистика игры
        stats_y = 120
        stats = [
            f"🎯 Финальный счет: {self.score}",
            f"📊 Слов переведено: {self.current_word_index}/{len(self.current_words)}",
            f"🔥 Максимальная серия: {self.max_streak}",
            f"📚 Новых слов выучено: {len([w for w in self.current_words if w in self.session_stats['words_learned']])}"
        ]
        
        for stat in stats:
            stat_surface = font.render(stat, True, WHITE)
            screen.blit(stat_surface, (WIDTH//2 - stat_surface.get_width()//2, stats_y))
            stats_y += 40
        
        # Обновление лучшего счета
        if self.score > self.session_stats["best_score"]:
            self.session_stats["best_score"] = self.score
            new_record = font.render("🏅 НОВЫЙ РЕКОРД!", True, GOLD)
            screen.blit(new_record, (WIDTH//2 - new_record.get_width()//2, stats_y))
            stats_y += 50
        
        # Кнопки
        restart_text = font.render("Нажмите R для новой игры", True, LIGHT_BLUE)
        menu_text = font.render("Нажмите M для возврата в меню", True, LIGHT_BLUE)
        
        screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT - 100))
        screen.blit(menu_text, (WIDTH//2 - menu_text.get_width()//2, HEIGHT - 60))

    def handle_menu_input(self, event):
        """Обработка ввода в меню"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return False
            
            # Выбор категории
            if event.unicode in self.word_categories:
                self.selected_category = event.unicode
                
            # Выбор уровня
            if event.unicode in self.levels:
                self.selected_level = event.unicode
                
            # Выбор режима
            if event.unicode in ["1", "2", "3"]:
                self.selected_mode = event.unicode
            
            # Запуск игры при наличии всех выборов
            if hasattr(self, 'selected_category') and hasattr(self, 'selected_level') and hasattr(self, 'selected_mode'):
                self.start_game(self.selected_category, self.selected_level, self.selected_mode)
                # Очищаем выбор для следующей игры
                delattr(self, 'selected_category')
                delattr(self, 'selected_level')
                delattr(self, 'selected_mode')
        
        return True

    def handle_game_input(self, event):
        """Обработка ввода во время игры"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.current_state = "menu"
                return True
            
            if event.key == pygame.K_SPACE and not self.recording and not self.waiting_for_input:
                # Начало записи
                self.recording = True
                self.recording_start_time = time.time()
                self.recording_duration = self.levels[self.current_level]["time_limit"]
                self.last_result = None
            
            if event.key == pygame.K_RETURN and self.waiting_for_input:
                # Переход к следующему слову
                self.waiting_for_input = False
                self.current_word_index += 1
                
                # Создаем новое изображение для следующего слова в визуальном режиме
                if self.game_mode == "3" and self.current_word_index < len(self.current_words):
                    next_word = self.current_words[self.current_word_index]
                    english_translation = self.word_categories[self.current_category]["words"][next_word]
                    self.current_image = self.create_unified_translation_image(next_word, english_translation, self.current_category)
                
                if self.current_word_index >= len(self.current_words):
                    self.current_state = "result"
                    self.save_stats()
        
        return True

    def handle_result_input(self, event):
        """Обработка ввода на экране результатов"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                # Новая игра с теми же настройками
                self.start_game(self.current_category, self.current_level, self.game_mode)
            elif event.key == pygame.K_m:
                self.current_state = "menu"
            elif event.key == pygame.K_ESCAPE:
                self.current_state = "menu"
        
        return True

    def update_game(self):
        """Обновление игрового состояния"""
        if self.current_state == "game" and self.recording:
            elapsed = time.time() - self.recording_start_time
            
            if elapsed >= self.recording_duration:
                # Завершение записи
                self.recording = False
                audio_file = self.record_audio(duration=self.recording_duration)
                user_answer = self.recognize_speech(audio_file)
                
                # Проверка ответа
                current_word_ru = self.current_words[self.current_word_index]
                current_category = self.word_categories[self.current_category]
                correct_answer = current_category["words"][current_word_ru]
                
                if user_answer and user_answer == correct_answer:
                    self.streak += 1
                    self.max_streak = max(self.max_streak, self.streak)
                    base_points = 10
                    streak_bonus = min(self.streak - 1, 5) * 2
                    level_bonus = int(base_points * (self.levels[self.current_level]["multiplier"] - 1))
                    points_earned = base_points + streak_bonus + level_bonus
                    
                    self.score += points_earned
                    self.session_stats["words_learned"].add(current_word_ru)
                    
                    self.last_result = {
                        "correct": True,
                        "message": f"✅ Правильно! +{points_earned} очков"
                    }
                    
                    # Проверка достижений
                    self.check_achievements()
                else:
                    self.streak = 0
                    if self.game_mode == "1":  # Классический режим
                        self.lives -= 1
                    
                    if user_answer:
                        self.last_result = {
                            "correct": False,
                            "message": f"❌ Неправильно. Вы сказали: '{user_answer}'"
                        }
                    else:
                        self.last_result = {
                            "correct": False,
                            "message": f"❌ Речь не распознана. Правильно: '{correct_answer}'"
                        }
                    
                    # Проверка окончания игры в классическом режиме
                    if self.game_mode == "1" and self.lives <= 0:
                        self.current_state = "result"
                        self.save_stats()
                        return
                
                self.waiting_for_input = True
                
                # Очистка временного файла
                if audio_file and os.path.exists(audio_file):
                    os.unlink(audio_file)

    def run(self):
        """Основной игровой цикл"""
        running = True
        clock = pygame.time.Clock()
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                # Обработка ввода в зависимости от состояния
                if self.current_state == "menu":
                    running = self.handle_menu_input(event)
                elif self.current_state == "game":
                    running = self.handle_game_input(event)
                elif self.current_state == "result":
                    running = self.handle_result_input(event)
            
            # Обновление игры
            self.update_game()
            
            # Отрисовка
            if self.current_state == "menu":
                self.draw_menu()
            elif self.current_state == "game":
                self.draw_game()
            elif self.current_state == "result":
                self.draw_result()
            
            pygame.display.flip()
            clock.tick(60)
        
        pygame.quit()
        sys.exit()

# Запуск игры
if __name__ == "__main__":
    game = SpeakingGame()
    game.run()