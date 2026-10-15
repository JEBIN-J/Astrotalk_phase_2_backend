import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dataset.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS palm_annotations (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        
        # Add new columns if they don't exist
        cursor = conn.execute("PRAGMA table_info(palm_annotations)")
        columns = [row['name'] for row in cursor.fetchall()]
        if 'original_image' not in columns:
            conn.execute("ALTER TABLE palm_annotations ADD COLUMN original_image TEXT")
        if 'annotated_image' not in columns:
            conn.execute("ALTER TABLE palm_annotations ADD COLUMN annotated_image TEXT")
            
        # Tarot tables
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tarot_daily_readings (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                card_id TEXT NOT NULL,
                orientation TEXT NOT NULL,
                seed TEXT NOT NULL,
                date TEXT NOT NULL,
                timezone REAL NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(user_id, date)
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tarot_readings_history (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                reading_type TEXT NOT NULL,
                question TEXT,
                spread_data TEXT NOT NULL,
                astrology_snapshot TEXT,
                seed TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        
        
        # Numerology tables
        conn.execute('''
            CREATE TABLE IF NOT EXISTS numerology_systems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                system_code TEXT UNIQUE NOT NULL,
                system_name TEXT NOT NULL,
                calculation_method TEXT NOT NULL,
                master_number_policy TEXT NOT NULL,
                version TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS life_path_interpretations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numerology_system_id INTEGER NOT NULL,
                life_path_number INTEGER NOT NULL,
                number_title TEXT NOT NULL,
                core_theme TEXT NOT NULL,
                overview TEXT NOT NULL,
                strengths TEXT NOT NULL,
                challenges TEXT NOT NULL,
                relationship_interpretation TEXT NOT NULL,
                career_interpretation TEXT NOT NULL,
                personal_growth_guidance TEXT NOT NULL,
                content_version TEXT NOT NULL DEFAULT '1.0.0',
                publication_status TEXT NOT NULL DEFAULT 'published',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (numerology_system_id) REFERENCES numerology_systems(id),
                UNIQUE(numerology_system_id, life_path_number, content_version)
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS life_path_interpretation_sections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interpretation_id INTEGER NOT NULL,
                section_type TEXT NOT NULL,
                heading TEXT NOT NULL,
                content TEXT NOT NULL,
                display_order INTEGER NOT NULL,
                publication_status TEXT NOT NULL DEFAULT 'published',
                FOREIGN KEY (interpretation_id) REFERENCES life_path_interpretations(id)
            )
        ''')

        
        # Birth Day Tables
        conn.execute('''
            CREATE TABLE IF NOT EXISTS birth_day_interpretations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numerology_system_id INTEGER NOT NULL,
                birth_day_number INTEGER NOT NULL,
                number_title TEXT NOT NULL,
                core_theme TEXT NOT NULL,
                overview TEXT NOT NULL,
                strengths TEXT NOT NULL,
                challenges TEXT NOT NULL,
                personality_interpretation TEXT NOT NULL,
                relationship_interpretation TEXT NOT NULL,
                career_interpretation TEXT NOT NULL,
                personal_growth_guidance TEXT NOT NULL,
                quick_summary TEXT NOT NULL,
                reduced_root INTEGER NOT NULL,
                content_version TEXT NOT NULL DEFAULT '1.0.0',
                publication_status TEXT NOT NULL DEFAULT 'published',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (numerology_system_id) REFERENCES numerology_systems(id),
                UNIQUE(numerology_system_id, birth_day_number, content_version)
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS birth_day_interpretation_sections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interpretation_id INTEGER NOT NULL,
                section_type TEXT NOT NULL,
                heading TEXT NOT NULL,
                content TEXT NOT NULL,
                display_order INTEGER NOT NULL,
                publication_status TEXT NOT NULL DEFAULT 'published',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (interpretation_id) REFERENCES birth_day_interpretations(id)
            )
        ''')


        # Remedies & Fixes Tables
        conn.execute('''
            CREATE TABLE IF NOT EXISTS numerology_remedy_systems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                system_code TEXT UNIQUE NOT NULL,
                system_name TEXT NOT NULL,
                methodology_version TEXT NOT NULL DEFAULT '1.0.0',
                description TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS numerology_remedies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                system_id INTEGER NOT NULL,
                remedy_code TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                traditional_association TEXT NOT NULL,
                explanation TEXT NOT NULL,
                instructions TEXT NOT NULL,
                precautions TEXT NOT NULL,
                affirmation TEXT,
                symbolic_color TEXT,
                symbolic_day TEXT,
                focus_area TEXT NOT NULL DEFAULT 'general',
                estimated_cost_category TEXT NOT NULL DEFAULT 'Zero Cost',
                is_optional INTEGER NOT NULL DEFAULT 1,
                content_version TEXT NOT NULL DEFAULT '1.0.0',
                publication_status TEXT NOT NULL DEFAULT 'published',
                reviewed_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (system_id) REFERENCES numerology_remedy_systems(id)
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS numerology_remedy_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                system_id INTEGER NOT NULL,
                rule_code TEXT UNIQUE NOT NULL,
                rule_description TEXT NOT NULL,
                input_number_type TEXT NOT NULL,
                condition_type TEXT NOT NULL,
                condition_value TEXT NOT NULL,
                priority INTEGER NOT NULL DEFAULT 10,
                publication_status TEXT NOT NULL DEFAULT 'published',
                rule_version TEXT NOT NULL DEFAULT '1.0.0',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (system_id) REFERENCES numerology_remedy_systems(id)
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS numerology_remedy_rule_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id INTEGER NOT NULL,
                remedy_id INTEGER NOT NULL,
                applicability_reason_template TEXT NOT NULL,
                display_order INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (rule_id) REFERENCES numerology_remedy_rules(id),
                FOREIGN KEY (remedy_id) REFERENCES numerology_remedies(id)
            )
        ''')

        # Learn Numerology Educational System Tables
        conn.execute('''
            CREATE TABLE IF NOT EXISTS numerology_learning_modules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_code TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                difficulty_level TEXT NOT NULL,
                display_order INTEGER NOT NULL,
                estimated_duration TEXT NOT NULL,
                language TEXT NOT NULL DEFAULT 'en',
                publication_status TEXT NOT NULL DEFAULT 'published',
                content_version TEXT NOT NULL DEFAULT '1.0.0',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS numerology_learning_lessons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_id INTEGER NOT NULL,
                lesson_code TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                introduction TEXT NOT NULL,
                learning_objectives TEXT NOT NULL,
                concept_content TEXT NOT NULL,
                formula_explanation TEXT,
                worked_examples TEXT,
                common_mistakes TEXT,
                practice_instructions TEXT,
                calculator_type TEXT,
                next_lesson_reference TEXT,
                language TEXT NOT NULL DEFAULT 'en',
                content_version TEXT NOT NULL DEFAULT '1.0.0',
                review_status TEXT NOT NULL DEFAULT 'approved',
                publication_status TEXT NOT NULL DEFAULT 'published',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (module_id) REFERENCES numerology_learning_modules(id)
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS numerology_learning_quizzes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lesson_id INTEGER NOT NULL,
                quiz_title TEXT NOT NULL,
                instructions TEXT NOT NULL,
                pass_threshold INTEGER NOT NULL DEFAULT 70,
                question_order TEXT NOT NULL DEFAULT 'sequential',
                publication_status TEXT NOT NULL DEFAULT 'published',
                FOREIGN KEY (lesson_id) REFERENCES numerology_learning_lessons(id)
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS numerology_learning_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_id INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                question_type TEXT NOT NULL DEFAULT 'multiple_choice',
                explanation TEXT NOT NULL,
                difficulty_level TEXT NOT NULL DEFAULT 'beginner',
                display_order INTEGER NOT NULL,
                review_status TEXT NOT NULL DEFAULT 'approved',
                is_active INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (quiz_id) REFERENCES numerology_learning_quizzes(id)
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS numerology_learning_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                answer_text TEXT NOT NULL,
                is_correct INTEGER NOT NULL DEFAULT 0,
                explanation TEXT,
                display_order INTEGER NOT NULL,
                FOREIGN KEY (question_id) REFERENCES numerology_learning_questions(id)
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS numerology_learning_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                lesson_id INTEGER NOT NULL,
                progress_status TEXT NOT NULL DEFAULT 'not_started',
                last_position INTEGER NOT NULL DEFAULT 0,
                completed_at TEXT,
                updated_at TEXT NOT NULL,
                UNIQUE(user_id, lesson_id),
                FOREIGN KEY (lesson_id) REFERENCES numerology_learning_lessons(id)
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS numerology_learning_quiz_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                quiz_id INTEGER NOT NULL,
                attempt_number INTEGER NOT NULL DEFAULT 1,
                answers_data TEXT NOT NULL,
                score REAL NOT NULL,
                submitted_at TEXT NOT NULL,
                result_status TEXT NOT NULL,
                FOREIGN KEY (quiz_id) REFERENCES numerology_learning_quizzes(id)
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS numerology_learning_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lesson_id INTEGER NOT NULL,
                source_title TEXT NOT NULL,
                source_url TEXT,
                source_type TEXT NOT NULL,
                attribution TEXT NOT NULL,
                licensing_notes TEXT NOT NULL,
                review_status TEXT NOT NULL DEFAULT 'approved',
                reviewed_at TEXT NOT NULL,
                FOREIGN KEY (lesson_id) REFERENCES numerology_learning_lessons(id)
            )
        ''')

        conn.execute('CREATE INDEX IF NOT EXISTS idx_num_lessons_module ON numerology_learning_lessons(module_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_num_progress_user ON numerology_learning_progress(user_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_num_quiz_lesson ON numerology_learning_quizzes(lesson_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_num_questions_quiz ON numerology_learning_questions(quiz_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_num_answers_question ON numerology_learning_answers(question_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_num_attempts_user ON numerology_learning_quiz_attempts(user_id)')

        # Angel Numbers Module Tables
        conn.execute('''
            CREATE TABLE IF NOT EXISTS angel_number_interpretations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sequence TEXT UNIQUE NOT NULL,
                canonical_sequence TEXT NOT NULL,
                title TEXT NOT NULL,
                short_meaning TEXT NOT NULL,
                detailed_meaning TEXT NOT NULL,
                traditional_symbolic_themes TEXT NOT NULL,
                reflection_questions TEXT NOT NULL,
                practical_guidance TEXT NOT NULL,
                love_and_relationships TEXT,
                career_and_work TEXT,
                personal_growth TEXT,
                spiritual_reflection TEXT,
                root_number INTEGER NOT NULL,
                primary_pattern TEXT NOT NULL,
                source_reference TEXT,
                content_version TEXT NOT NULL DEFAULT '1.0.0',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS angel_number_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_code TEXT UNIQUE NOT NULL,
                pattern_name TEXT NOT NULL,
                pattern_description TEXT NOT NULL,
                display_priority INTEGER NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS angel_number_sightings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                observed_sequence TEXT NOT NULL,
                observed_at TEXT NOT NULL,
                timezone TEXT NOT NULL DEFAULT 'UTC',
                context_category TEXT,
                personal_note TEXT,
                mood TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS angel_number_daily_content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sequence TEXT NOT NULL,
                title TEXT NOT NULL,
                reflection TEXT NOT NULL,
                day_of_year_index INTEGER NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        conn.execute('CREATE INDEX IF NOT EXISTS idx_angel_seq ON angel_number_interpretations(sequence)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_angel_root ON angel_number_interpretations(root_number)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_angel_sightings_user ON angel_number_sightings(user_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_angel_daily_day ON angel_number_daily_content(day_of_year_index)')

        
        # Match Making Module Tables
        conn.execute('''
            CREATE TABLE IF NOT EXISTS astrology_calculation_methods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                method_code TEXT UNIQUE NOT NULL,
                method_name TEXT NOT NULL,
                engine_version TEXT NOT NULL,
                ayanamsha_code TEXT NOT NULL DEFAULT 'LAHIRI',
                zodiac_convention TEXT NOT NULL DEFAULT 'SIDEREAL',
                configuration_json TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS matching_rule_sets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                method_code TEXT NOT NULL,
                regional_tradition TEXT NOT NULL,
                rule_set_version TEXT NOT NULL DEFAULT '1.0.0',
                effective_date TEXT NOT NULL,
                source_reference TEXT,
                review_status TEXT NOT NULL DEFAULT 'approved',
                is_active INTEGER NOT NULL DEFAULT 1
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS matching_factor_definitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_set_id INTEGER NOT NULL,
                factor_code TEXT NOT NULL,
                factor_name TEXT NOT NULL,
                maximum_score REAL,
                calculation_type TEXT NOT NULL,
                display_order INTEGER NOT NULL,
                rule_configuration TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (rule_set_id) REFERENCES matching_rule_sets(id)
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS matching_interpretations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_set_id INTEGER NOT NULL,
                factor_code TEXT NOT NULL,
                result_category TEXT NOT NULL,
                title TEXT NOT NULL,
                short_explanation TEXT NOT NULL,
                detailed_explanation TEXT NOT NULL,
                practical_guidance TEXT NOT NULL,
                language TEXT NOT NULL DEFAULT 'en',
                content_version TEXT NOT NULL DEFAULT '1.0.0',
                review_status TEXT NOT NULL DEFAULT 'approved',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS saved_matching_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                authorized_owner_user_id TEXT,
                boy_name TEXT NOT NULL,
                girl_name TEXT NOT NULL,
                method_code TEXT NOT NULL,
                rule_set_version TEXT NOT NULL,
                engine_version TEXT NOT NULL,
                total_score REAL NOT NULL,
                max_score REAL NOT NULL,
                status TEXT NOT NULL,
                report_result_data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        conn.execute('CREATE INDEX IF NOT EXISTS idx_matching_methods_code ON astrology_calculation_methods(method_code)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_matching_rulesets_trad ON matching_rule_sets(regional_tradition)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_matching_factors_code ON matching_factor_definitions(factor_code)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_matching_interp_factor ON matching_interpretations(factor_code, result_category)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_matching_saved_user ON saved_matching_reports(authorized_owner_user_id)')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS user_remedy_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                preferred_categories TEXT,
                excluded_categories TEXT,
                focus_area TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        conn.commit()
    finally:
        conn.close()

# Initialize tables on import
init_db()

def save_palm_annotation(record_id: str, data: dict, created_at: str, original_image: str = None, annotated_image: str = None):
    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO palm_annotations (id, data, created_at, original_image, annotated_image) VALUES (?, ?, ?, ?, ?)',
            (record_id, json.dumps(data), created_at, original_image, annotated_image)
        )

        # Remedies & Fixes Tables
        conn.execute('''
            CREATE TABLE IF NOT EXISTS numerology_remedy_systems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                system_code TEXT UNIQUE NOT NULL,
                system_name TEXT NOT NULL,
                methodology_version TEXT NOT NULL DEFAULT '1.0.0',
                description TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS numerology_remedies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                system_id INTEGER NOT NULL,
                remedy_code TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                traditional_association TEXT NOT NULL,
                explanation TEXT NOT NULL,
                instructions TEXT NOT NULL,
                precautions TEXT NOT NULL,
                affirmation TEXT,
                symbolic_color TEXT,
                symbolic_day TEXT,
                focus_area TEXT NOT NULL DEFAULT 'general',
                estimated_cost_category TEXT NOT NULL DEFAULT 'Zero Cost',
                is_optional INTEGER NOT NULL DEFAULT 1,
                content_version TEXT NOT NULL DEFAULT '1.0.0',
                publication_status TEXT NOT NULL DEFAULT 'published',
                reviewed_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (system_id) REFERENCES numerology_remedy_systems(id)
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS numerology_remedy_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                system_id INTEGER NOT NULL,
                rule_code TEXT UNIQUE NOT NULL,
                rule_description TEXT NOT NULL,
                input_number_type TEXT NOT NULL,
                condition_type TEXT NOT NULL,
                condition_value TEXT NOT NULL,
                priority INTEGER NOT NULL DEFAULT 10,
                publication_status TEXT NOT NULL DEFAULT 'published',
                rule_version TEXT NOT NULL DEFAULT '1.0.0',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (system_id) REFERENCES numerology_remedy_systems(id)
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS numerology_remedy_rule_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id INTEGER NOT NULL,
                remedy_id INTEGER NOT NULL,
                applicability_reason_template TEXT NOT NULL,
                display_order INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (rule_id) REFERENCES numerology_remedy_rules(id),
                FOREIGN KEY (remedy_id) REFERENCES numerology_remedies(id)
            )
        ''')

        # Learn Numerology Educational System Tables
        conn.execute('''
            CREATE TABLE IF NOT EXISTS numerology_learning_modules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_code TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                difficulty_level TEXT NOT NULL,
                display_order INTEGER NOT NULL,
                estimated_duration TEXT NOT NULL,
                language TEXT NOT NULL DEFAULT 'en',
                publication_status TEXT NOT NULL DEFAULT 'published',
                content_version TEXT NOT NULL DEFAULT '1.0.0',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS numerology_learning_lessons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_id INTEGER NOT NULL,
                lesson_code TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                introduction TEXT NOT NULL,
                learning_objectives TEXT NOT NULL,
                concept_content TEXT NOT NULL,
                formula_explanation TEXT,
                worked_examples TEXT,
                common_mistakes TEXT,
                practice_instructions TEXT,
                calculator_type TEXT,
                next_lesson_reference TEXT,
                language TEXT NOT NULL DEFAULT 'en',
                content_version TEXT NOT NULL DEFAULT '1.0.0',
                review_status TEXT NOT NULL DEFAULT 'approved',
                publication_status TEXT NOT NULL DEFAULT 'published',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (module_id) REFERENCES numerology_learning_modules(id)
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS numerology_learning_quizzes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lesson_id INTEGER NOT NULL,
                quiz_title TEXT NOT NULL,
                instructions TEXT NOT NULL,
                pass_threshold INTEGER NOT NULL DEFAULT 70,
                question_order TEXT NOT NULL DEFAULT 'sequential',
                publication_status TEXT NOT NULL DEFAULT 'published',
                FOREIGN KEY (lesson_id) REFERENCES numerology_learning_lessons(id)
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS numerology_learning_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_id INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                question_type TEXT NOT NULL DEFAULT 'multiple_choice',
                explanation TEXT NOT NULL,
                difficulty_level TEXT NOT NULL DEFAULT 'beginner',
                display_order INTEGER NOT NULL,
                review_status TEXT NOT NULL DEFAULT 'approved',
                is_active INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (quiz_id) REFERENCES numerology_learning_quizzes(id)
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS numerology_learning_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                answer_text TEXT NOT NULL,
                is_correct INTEGER NOT NULL DEFAULT 0,
                explanation TEXT,
                display_order INTEGER NOT NULL,
                FOREIGN KEY (question_id) REFERENCES numerology_learning_questions(id)
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS numerology_learning_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                lesson_id INTEGER NOT NULL,
                progress_status TEXT NOT NULL DEFAULT 'not_started',
                last_position INTEGER NOT NULL DEFAULT 0,
                completed_at TEXT,
                updated_at TEXT NOT NULL,
                UNIQUE(user_id, lesson_id),
                FOREIGN KEY (lesson_id) REFERENCES numerology_learning_lessons(id)
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS numerology_learning_quiz_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                quiz_id INTEGER NOT NULL,
                attempt_number INTEGER NOT NULL DEFAULT 1,
                answers_data TEXT NOT NULL,
                score REAL NOT NULL,
                submitted_at TEXT NOT NULL,
                result_status TEXT NOT NULL,
                FOREIGN KEY (quiz_id) REFERENCES numerology_learning_quizzes(id)
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS numerology_learning_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lesson_id INTEGER NOT NULL,
                source_title TEXT NOT NULL,
                source_url TEXT,
                source_type TEXT NOT NULL,
                attribution TEXT NOT NULL,
                licensing_notes TEXT NOT NULL,
                review_status TEXT NOT NULL DEFAULT 'approved',
                reviewed_at TEXT NOT NULL,
                FOREIGN KEY (lesson_id) REFERENCES numerology_learning_lessons(id)
            )
        ''')

        conn.execute('CREATE INDEX IF NOT EXISTS idx_num_lessons_module ON numerology_learning_lessons(module_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_num_progress_user ON numerology_learning_progress(user_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_num_quiz_lesson ON numerology_learning_quizzes(lesson_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_num_questions_quiz ON numerology_learning_questions(quiz_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_num_answers_question ON numerology_learning_answers(question_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_num_attempts_user ON numerology_learning_quiz_attempts(user_id)')

        # Angel Numbers Module Tables
        conn.execute('''
            CREATE TABLE IF NOT EXISTS angel_number_interpretations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sequence TEXT UNIQUE NOT NULL,
                canonical_sequence TEXT NOT NULL,
                title TEXT NOT NULL,
                short_meaning TEXT NOT NULL,
                detailed_meaning TEXT NOT NULL,
                traditional_symbolic_themes TEXT NOT NULL,
                reflection_questions TEXT NOT NULL,
                practical_guidance TEXT NOT NULL,
                love_and_relationships TEXT,
                career_and_work TEXT,
                personal_growth TEXT,
                spiritual_reflection TEXT,
                root_number INTEGER NOT NULL,
                primary_pattern TEXT NOT NULL,
                source_reference TEXT,
                content_version TEXT NOT NULL DEFAULT '1.0.0',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS angel_number_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_code TEXT UNIQUE NOT NULL,
                pattern_name TEXT NOT NULL,
                pattern_description TEXT NOT NULL,
                display_priority INTEGER NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS angel_number_sightings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                observed_sequence TEXT NOT NULL,
                observed_at TEXT NOT NULL,
                timezone TEXT NOT NULL DEFAULT 'UTC',
                context_category TEXT,
                personal_note TEXT,
                mood TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS angel_number_daily_content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sequence TEXT NOT NULL,
                title TEXT NOT NULL,
                reflection TEXT NOT NULL,
                day_of_year_index INTEGER NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        conn.execute('CREATE INDEX IF NOT EXISTS idx_angel_seq ON angel_number_interpretations(sequence)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_angel_root ON angel_number_interpretations(root_number)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_angel_sightings_user ON angel_number_sightings(user_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_angel_daily_day ON angel_number_daily_content(day_of_year_index)')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS user_remedy_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                preferred_categories TEXT,
                excluded_categories TEXT,
                focus_area TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        conn.commit()
    finally:
        conn.close()
