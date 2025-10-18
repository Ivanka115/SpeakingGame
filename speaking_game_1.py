import speech_recognition as sr
import sounddevice as sd
from scipy.io.wavfile import write
import tempfile
import os
import random
import time
import sys
import json
from datetime import datetime
import wave
import numpy as np

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
        
        # Тематические наборы слов
        self.word_categories = {
            "1": {"name": "Базовые слова", "words": {
                "кот": "cat", "собака": "dog", "дом": "house", "солнце": "sun",
                "вода": "water", "книга": "book", "стол": "table", "окно": "window",
                "яблоко": "apple", "машина": "car", "рука": "hand", "нога": "leg"
            }},
            "2": {"name": "Еда и напитки", "words": {
                "хлеб": "bread", "молоко": "milk", "чай": "tea", "кофе": "coffee",
                "суп": "soup", "сыр": "cheese", "мясо": "meat", "рыба": "fish",
                "фрукты": "fruits", "овощи": "vegetables", "салат": "salad"
            }},
            "3": {"name": "Природа и животные", "words": {
                "дерево": "tree", "цветок": "flower", "птица": "bird", "лес": "forest",
                "река": "river", "море": "sea", "горы": "mountains", "небо": "sky",
                "звезда": "star", "луна": "moon", "погода": "weather"
            }},
            "4": {"name": "Город и транспорт", "words": {
                "город": "city", "улица": "street", "парк": "park", "магазин": "shop",
                "школа": "school", "больница": "hospital", "автобус": "bus",
                "поезд": "train", "самолет": "airplane", "велосипед": "bicycle"
            }}
        }
        
        # Система достижений
        self.achievements = {
            "first_blood": {"name": "Первая кровь", "desc": "Завершите первую игру", "earned": False},
            "streak_master": {"name": "Мастер серии", "desc": "Достигните серии из 5 правильных ответов", "earned": False},
            "perfectionist": {"name": "Перфекционист", "desc": "Пройдите уровень без ошибок", "earned": False},
            "vocabulary": {"name": "Словарный запас", "desc": "Выучите 20 слов", "earned": False},
            "speed_demon": {"name": "Скоростной демон", "desc": "Пройдите экспертный уровень", "earned": False}
        }

    def load_stats(self):
        """Загрузка статистики из файла"""
        try:
            with open("game_stats.json", "r", encoding = "utf-8") as f:
                self.session_stats = json.load(f)
                # Преобразование set обратно из list
                self.session_stats["words_learned"] = set(self.session_stats.get("words_learned", []))
        except FileNotFoundError:
            pass

    def save_stats(self):
        """Сохранение статистики в файл"""
        try:
            stats_to_save = self.session_stats.copy()
            stats_to_save["words_learned"] = list(stats_to_save["words_learned"])
            with open("game_stats.json", "w", encoding = "utf-8") as f:
                json.dump(stats_to_save, f, ensure_ascii = False, indent = 2)
        except Exception as e:
            print(f"⚠️ Не удалось сохранить статистику: {e}")

    def analyze_pronunciation(self, audio_file, correct_word):
        """Анализ произношения (упрощенная версия)"""
        try:
            with wave.open(audio_file, 'rb') as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                duration = frames / float(rate)
                
                # Читаем аудиоданные
                signal = wav_file.readframes(frames)
                audio_data = np.frombuffer(signal, dtype = np.int16)
                
                # Простой анализ громкости
                volume = np.sqrt(np.mean(audio_data**2))
                
                feedback = []
                
                # Проверка длительности
                if duration < 0.5:
                    feedback.append("🗣️ Слишком коротко")
                elif duration > 3.0:
                    feedback.append("🗣️ Слишком долго")
                else:
                    feedback.append("🗣️ Хорошая длительность")
                
                # Проверка громкости
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
        
        # Первая игра
        if not self.achievements["first_blood"]["earned"] and self.session_stats["games_played"] > 0:
            self.achievements["first_blood"]["earned"] = True
            new_achievements.append("first_blood")
        
        # Серия из 5 правильных ответов
        if not self.achievements["streak_master"]["earned"] and self.streak >= 5:
            self.achievements["streak_master"]["earned"] = True
            new_achievements.append("streak_master")
        
        # 20 выученных слов
        if not self.achievements["vocabulary"]["earned"] and len(self.session_stats["words_learned"]) >= 20:
            self.achievements["vocabulary"]["earned"] = True
            new_achievements.append("vocabulary")
        
        return new_achievements

    def show_achievements(self, new_ones = None):
        """Показ достижений"""
        print(f"\n🏆 ДОСТИЖЕНИЯ ({sum(1 for a in self.achievements.values() if a['earned'])}/{len(self.achievements)})")
        print("=" * 50)
        
        for achievement in self.achievements.values():
            status = "✅" if achievement["earned"] else "❌"
            print(f"{status} {achievement['name']}: {achievement['desc']}")
        
        if new_ones:
            print(f"\n🎉 Новые достижения!")
            for ach_id in new_ones:
                ach = self.achievements[ach_id]
                print(f"   🎊 {ach['name']}: {ach['desc']}")

    def record_audio(self, duration = 5, sample_rate = 44100):
        """Запись аудио с микрофона"""
        print("\n🎤 Запись начинается... Говорите!")
        try:
            audio_data = sd.rec(int(duration * sample_rate), samplerate = sample_rate, channels = 1, dtype = 'int16')
            sd.wait()
            
            with tempfile.NamedTemporaryFile(suffix = '.wav', delete = False) as tmp_file:
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
                self.recognizer.adjust_for_ambient_noise(source, duration = 0.5)
                audio = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio, language = 'en-US')
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

    def show_ascii_art(self, state):
        """Показ ASCII графики"""
        arts = {
            "welcome": r"""
                ╔══════════════════════════════════════╗
                ║           ГОВОРИ ПРАВИЛЬНО           ║
                ║           SPEAK CORRECTLY            ║
                ║      🎯 Учись. Говори. Побеждай! 🎯 ║
                ╚══════════════════════════════════════╝
            """,
            "correct": r"""
            🎉 ПРАВИЛЬНО! 🎉
               \
                \
                 👏
                /|\
                / \
            """,
            "wrong": r"""
            ❌ НЕПРАВИЛЬНО 
               \
                \
                 😞
                /|\
                / \
            """,
            "game_over": r"""
                ╔══════════════════════════════╗
                ║         ИГРА ОКОНЧЕНА        ║
                ║          GAME OVER           ║
                ╚══════════════════════════════╝
            """,
            "microphone": r"""
              🎤
             ┌───┐
             │   │
             └───┘
              │ │
              │ │
            """
        }
        print(arts.get(state, ""))

    def show_progress(self, current, total, score, lives, streak):
        """Показ прогресса игры"""
        progress = int((current / total) * 20)
        bar = "█" * progress + "░" * (20 - progress)
        print(f"\n📊 Прогресс: [{bar}] {current}/{total}")
        print(f"🎯 Счет: {score} | ❤️  Жизни: {'♥ ' * lives} | 🔥 Серия: {streak}")

    def show_stats(self):
        """Показать статистику игрока"""
        print(f"\n📈 ВАША СТАТИСТИКА")
        print("=" * 40)
        print(f"🎮 Игр сыграно: {self.session_stats['games_played']}")
        print(f"🏆 Лучший счет: {self.session_stats['best_score']}")
        print(f"📚 Слов выучено: {len(self.session_stats['words_learned'])}")
        print(f"💎 Макс. серия: {self.max_streak}")

    def choose_category(self):
        """Выбор категории слов"""
        print(f"\n📚 ВЫБЕРИТЕ КАТЕГОРИЮ СЛОВ:")
        for key, category in self.word_categories.items():
            print(f"   {key}. {category['name']} ({len(category['words'])} слов)")
        
        while True:
            choice = input("\nВаш выбор (1-4): ").strip()
            if choice in self.word_categories:
                return choice
            print("❌ Пожалуйста, выберите от 1 до 4")

    def choose_mode(self):
        """Выбор режима игры"""
        print(f"\n🎮 ВЫБЕРИТЕ РЕЖИМ ИГРЫ:")
        print("   1. 🎯 Классический режим (с жизнями)")
        print("   2. 🏋️  Тренировочный режим (без жизней)")
        
        while True:
            choice = input("\nВаш выбор (1-2): ").strip()
            if choice in ["1", "2"]:
                return choice
            print("❌ Пожалуйста, выберите 1 или 2")

    def play_game(self):
        """Основной игровой цикл"""
        self.show_ascii_art("welcome")
        
        # Обновление статистики
        self.session_stats["games_played"] += 1
        
        # Выбор режима
        game_mode = self.choose_mode()
        is_training = game_mode == "2"
        
        if is_training:
            print("\n🏋️  ТРЕНАЖЕР: Практикуйтесь без ограничений!")
            self.lives = 999  # Бесконечные жизни в тренировочном режиме
        
        # Выбор категории
        category_id = self.choose_category()
        category = self.word_categories[category_id]
        
        # Выбор уровня сложности
        print(f"\n🎚️  ВЫБЕРИТЕ УРОВЕНЬ СЛОЖНОСТИ:")
        for key, level in self.levels.items():
            print(f"   {key}. {level['name']} ({level['words']} слов, время: {level['time_limit']} сек)")
        
        while True:
            level_choice = input("\nВаш выбор (1-3): ").strip()
            if level_choice in self.levels:
                break
            print("❌ Пожалуйста, выберите 1, 2 или 3")
        
        current_level = self.levels[level_choice]
        words = self.get_word_list(category_id, level_choice)
        
        print(f"\n🚀 НАЧИНАЕМ!")
        print(f"📚 Категория: {category['name']}")
        print(f"🎯 Уровень: {current_level['name']}")
        print(f"🔤 Слов для перевода: {len(words)}")
        print(f"⏱️  Время на ответ: {current_level['time_limit']} секунд")
        
        if not is_training:
            print("❤️  Жизни: " + "♥ " * self.lives)
        
        input("\nНажмите Enter чтобы начать...")
        
        # Игровой цикл
        perfect_game = True
        for i, word_ru in enumerate(words, 1):
            print(f"\n{'='*50}")
            self.show_progress(i, len(words), self.score, self.lives if not is_training else 999, self.streak)
            print(f"\n🔤 Русское слово: {word_ru.upper()}")
            print(f"⏱️  У вас {current_level['time_limit']} секунд...")
            
            correct_answer = category["words"][word_ru]
            self.show_ascii_art("microphone")
            
            # Запись и распознавание
            audio_file = self.record_audio(duration=current_level['time_limit'])
            user_answer = self.recognize_speech(audio_file)
            
            # Анализ произношения
            pronunciation_feedback = self.analyze_pronunciation(audio_file, correct_answer) if audio_file else []
            
            # Проверка ответа
            if user_answer and user_answer == correct_answer:
                self.streak += 1
                self.max_streak = max(self.max_streak, self.streak)
                base_points = 10
                streak_bonus = min(self.streak - 1, 5) * 2  # Бонус за серию до +10
                level_bonus = int(base_points * (current_level["multiplier"] - 1))
                points_earned = base_points + streak_bonus + level_bonus
                
                self.score += points_earned
                self.session_stats["words_learned"].add(word_ru)
                
                self.show_ascii_art("correct")
                print(f"✅ Отлично! Вы сказали: '{user_answer}'")
                print(f"🎯 +{points_earned} очков! (10 базовых + {streak_bonus} за серию + {level_bonus} за уровень)")
                print(f"💎 Текущий счет: {self.score} | 🔥 Серия: {self.streak}")
                
                # Показать фидбек по произношению
                for feedback in pronunciation_feedback:
                    print(f"   {feedback}")
                    
            else:
                self.streak = 0
                perfect_game = False
                
                if not is_training:
                    self.lives -= 1
                
                self.show_ascii_art("wrong")
                if user_answer:
                    print(f"❌ Вы сказали: '{user_answer}'")
                else:
                    print("❌ Речь не распознана или ответ неверный")
                print(f"💡 Правильный ответ: '{correct_answer}'")
                
                # Показать фидбек по произношению даже при ошибке
                for feedback in pronunciation_feedback:
                    print(f"   {feedback}")
                
                if not is_training:
                    print(f"❤️  Осталось жизней: {self.lives}")
                
                # Проверка на game over (только в классическом режиме)
                if not is_training and self.lives <= 0:
                    self.show_ascii_art("game_over")
                    print(f"💔 Игра окончена! Ваш счет: {self.score}")
                    break
            
            # Пауза между словами
            if i < len(words) and (is_training or self.lives > 0):
                print("\nПодготовьтесь к следующему слову...")
                for countdown in range(2, 0, -1):
                    print(f"⏰ {countdown}...", end = " ")
                    sys.stdout.flush()
                    time.sleep(1)
                print()
        
        # Завершение игры
        if is_training or self.lives > 0:
            print(f"\n🎊 Поздравляем! Вы завершили {category['name']}!")
            print(f"🏆 Ваш финальный счет: {self.score}")
            
            # Бонусы
            if perfect_game and not is_training:
                perfect_bonus = 50
                self.score += perfect_bonus
                print(f"⭐ Бонус за идеальную игру: +{perfect_bonus} очков!")
            
            if not is_training:
                lives_bonus = self.lives * int(level_choice) * 5
                self.score += lives_bonus
                print(f"🎁 Бонус за жизни: +{lives_bonus} очков")
            
            print(f"💎 Итоговый счет: {self.score}")
            
            # Обновление лучшего счета
            if self.score > self.session_stats["best_score"]:
                self.session_stats["best_score"] = self.score
                print("🏅 Новый рекорд!")
        
        # Проверка достижений
        new_achievements = self.check_achievements()
        
        # Показать статистику
        self.show_stats()
        
        # Показать достижения
        self.show_achievements(new_achievements)
        
        # Сохранить статистику
        self.save_stats()
        
        # Предложение сыграть еще раз
        print(f"\n{'=' * 50}")
        play_again = input("\n🎮 Хотите сыграть еще раз? (да/нет): ").lower()
        if play_again in ['да', 'д', 'yes', 'y', '1']:
            self.score = 0
            self.streak = 0
            self.lives = 3
            self.play_game()
        else:
            print("\nСпасибо за игру! До встречи! 👋")
            print("Ваш прогресс сохранен.")

# Запуск игры
if __name__ == "__main__":
    try:
        game = SpeakingGame()
        game.play_game()
    except KeyboardInterrupt:
        print("\n\nИгра прервана. До свидания! 👋")
    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {e}")
        print("Пожалуйста, проверьте:")
        print("1. Подключение к интернету")
        print("2. Наличие микрофона")
        print("3. Разрешения для доступа к микрофону")