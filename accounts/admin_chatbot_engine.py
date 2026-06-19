# -*- coding: utf-8 -*-
"""
Chatbot Helper — Motor principal del asistente de administración.

Flujo:
  inicio           → menú principal (módulos filtrados por rol)
  menu_<mod>       → subsecciones del módulo como botones
  <section_id>     → contenido final de la sección
  texto libre      → búsqueda por keywords en todas las secciones accesibles
"""
import re
from .models import AdminChatLog
from .helper_manual import MODULES, get_all_searchable_entries


class AdminChatEngine:

    def __init__(self):
        self._search_index = get_all_searchable_entries()

    # ──────────────────────────────────────────────
    # Utilidades
    # ──────────────────────────────────────────────
    @staticmethod
    def normalize(text):
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        return set(text.split())

    def _user_can_see(self, user, roles_list):
        """Check if user matches any of the allowed roles for a module."""
        if 'all' in roles_list:
            return True
        if user.is_superadmin and 'superadmin' in roles_list:
            return True
        if user.is_transportista:
            return 'transportista' in roles_list
        # Staff (admins that are NOT transportistas)
        if user.is_staff:
            return 'staff' in roles_list or 'superadmin' in roles_list and user.is_superadmin
        return False

    def _back_button(self, target='inicio'):
        """Returns a 'go back' button."""
        label = '← Volver al inicio' if target == 'inicio' else '← Volver'
        return {'label': label, 'value': target}

    def _log(self, user, question, answer, intent):
        AdminChatLog.objects.create(
            user=user,
            question=question,
            answer=answer[:500],
            intent=intent
        )

    # ──────────────────────────────────────────────
    # Punto de entrada
    # ──────────────────────────────────────────────
    def process(self, message, user, path=''):
        msg = message.strip()

        # 1. Comando "inicio" → menú principal
        if msg.lower() == 'inicio':
            return self._handle_main_menu(user, msg)

        # 2. Comando "menu_<mod>" → subsecciones del módulo
        if msg.startswith('menu_'):
            return self._handle_module_menu(user, msg)

        # 3. Comando semántico de sección (e.g. "client_catalogo")
        section_result = self._handle_section(user, msg)
        if section_result:
            return section_result

        # 4. Fallback: búsqueda libre por keywords
        return self._handle_free_search(user, msg)

    # ──────────────────────────────────────────────
    # 1. Menú principal
    # ──────────────────────────────────────────────
    def _handle_main_menu(self, user, raw_msg):
        buttons = []
        for mod_id, mod_data in MODULES.items():
            if self._user_can_see(user, mod_data['roles']):
                buttons.append({
                    'label': mod_data['title'],
                    'value': f'menu_{mod_id}'
                })

        answer = (
            "¡Hola! Soy **Helper**, tu asistente del panel. "
            "¿Sobre qué módulo te gustaría obtener información?"
        )
        self._log(user, raw_msg, answer, 'greeting')
        return {
            'messages': [{'text': answer}],
            'buttons': buttons,
            'intent': 'greeting',
            'confidence': 1.0,
        }

    # ──────────────────────────────────────────────
    # 2. Menú de módulo → muestra subsecciones
    # ──────────────────────────────────────────────
    def _handle_module_menu(self, user, raw_msg):
        mod_id = raw_msg.split('menu_', 1)[1]
        mod_data = MODULES.get(mod_id)

        if not mod_data or not self._user_can_see(user, mod_data['roles']):
            answer = "No tienes acceso a este módulo o no existe."
            self._log(user, raw_msg, answer, 'denied')
            return {
                'messages': [{'text': answer}],
                'buttons': [self._back_button()],
                'intent': 'denied',
                'confidence': 1.0,
            }

        buttons = []
        for sec_id, sec_data in mod_data['sections'].items():
            buttons.append({
                'label': sec_data['label'],
                'value': sec_id,
            })
        buttons.append(self._back_button())

        answer = f"**{mod_data['title']}**\n\nSelecciona un tema:"
        self._log(user, raw_msg, answer, mod_id)
        return {
            'messages': [{'text': answer}],
            'buttons': buttons,
            'intent': mod_id,
            'confidence': 1.0,
        }

    # ──────────────────────────────────────────────
    # 3. Sección individual → contenido final
    # ──────────────────────────────────────────────
    def _handle_section(self, user, raw_msg):
        for mod_id, mod_data in MODULES.items():
            if raw_msg in mod_data['sections']:
                if not self._user_can_see(user, mod_data['roles']):
                    answer = "No tienes acceso a esta información."
                    self._log(user, raw_msg, answer, 'denied')
                    return {
                        'messages': [{'text': answer}],
                        'buttons': [self._back_button()],
                        'intent': 'denied',
                        'confidence': 1.0,
                    }

                sec_data = mod_data['sections'][raw_msg]
                answer = sec_data['content']
                self._log(user, raw_msg, answer, raw_msg)
                return {
                    'messages': [{'text': answer}],
                    'buttons': [
                        {'label': f'← Volver a {mod_data["title"]}', 'value': f'menu_{mod_id}'},
                        self._back_button(),
                    ],
                    'intent': raw_msg,
                    'confidence': 1.0,
                }
        return None  # Not a known section → let fallback handle it

    # ──────────────────────────────────────────────
    # 4. Búsqueda libre (fallback)
    # ──────────────────────────────────────────────
    def _handle_free_search(self, user, raw_msg):
        user_tokens = self.normalize(raw_msg)
        if not user_tokens:
            return self._fallback_response(user, raw_msg)

        best_entry = None
        best_score = 0

        for entry in self._search_index:
            # Skip entries the user can't see
            if not self._user_can_see(user, entry['roles']):
                continue

            kw_set = set(entry['keywords'])
            matches = user_tokens.intersection(kw_set)
            if not matches:
                # Secondary: check if any user token appears in the content
                content_tokens = self.normalize(entry['content'])
                content_matches = user_tokens.intersection(content_tokens)
                if len(content_matches) >= 2:
                    score = len(content_matches) / len(user_tokens) * 0.5  # lower weight
                else:
                    continue
            else:
                # Primary score: ratio of matched keywords to user tokens
                score = len(matches) / len(user_tokens)

            if score > best_score:
                best_score = score
                best_entry = entry

        if best_entry and best_score >= 0.1:
            answer = best_entry['content']
            mod_id = best_entry['module_id']
            mod_data = MODULES[mod_id]
            intent = best_entry['section_id']
            self._log(user, raw_msg, answer, intent)
            return {
                'messages': [{'text': answer}],
                'buttons': [
                    {'label': f'← Volver a {mod_data["title"]}', 'value': f'menu_{mod_id}'},
                    self._back_button(),
                ],
                'intent': intent,
                'confidence': round(best_score, 2),
            }

        return self._fallback_response(user, raw_msg)

    def _fallback_response(self, user, raw_msg):
        answer = (
            "No estoy seguro de entenderte. Intenta navegar usando los botones "
            "o reformula tu pregunta.\n\n"
            "También puedes escribir **\"inicio\"** para ver el menú principal."
        )
        self._log(user, raw_msg, answer, 'unknown')
        return {
            'messages': [{'text': answer}],
            'buttons': [self._back_button()],
            'intent': 'unknown',
            'confidence': 0.0,
        }
