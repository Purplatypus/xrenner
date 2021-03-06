"""
xrenner - eXternally configurable REference and Non Named Entity Recognizer
modules/xrenner_classes.py
Basic classes for parsed tokens, markables and sentences.
Author: Amir Zeldes
"""

import sys

class ParsedToken:
	def __init__(self, tok_id, text, lemma, pos, morph, head, func, sentence, modifiers, child_funcs, child_strings, lex, quoted=False):
		self.id = tok_id
		self.text = text
		self.pos = pos
		if lemma != "_" and lemma != "--":
			self.lemma = lemma
		else:
			self.lemma = lex.lemmatize(self)
		self.morph = morph
		if morph != "_" and morph != "--":
			self.morph = lex.process_morph(self)

		self.head = head
		self.original_head = head
		self.func = func
		self.sentence = sentence
		self.modifiers = modifiers
		self.child_funcs = child_funcs
		self.child_strings = child_strings
		self.quoted = quoted
		self.coordinate = False
		self.head_text = ""

	def __repr__(self):
		return str(self.text) + " (" + str(self.pos) + "/" + str(self.lemma) + ") " + "<-" + str(self.func) + "- " + str(self.head_text)

class Markable:
	def __init__(self, mark_id, head, form, definiteness, start, end, text, core_text, entity, entity_certainty, subclass, infstat, agree, sentence,
				 antecedent, coref_type, group, alt_entities, alt_subclasses, alt_agree,cardinality=0, submarks=[], coordinate=False):
		self.id = mark_id
		self.head = head
		self.form = form
		self.definiteness = definiteness
		self.start = start
		self.end = end
		self.text = text
		self.core_text = core_text  # Holds markable text before any extensions or manipulations
		self.entity = entity
		self.subclass = subclass
		self.infstat = infstat
		self.agree = agree
		self.agree_certainty = ""
		self.sentence = sentence
		self.antecedent = antecedent
		self.coref_type = coref_type
		self.group = group
		self.non_antecdent_groups = set()
		self.entity_certainty = entity_certainty
		self.isa_partner_head = ""  # Property to hold isa match; once saturated, no other lexeme may form isa link

		# Alternate agreement, subclass and entity lists:
		self.alt_agree = alt_agree
		self.alt_entities = alt_entities
		self.alt_subclasses = alt_subclasses

		self.cardinality=cardinality
		self.submarks = submarks
		self.coordinate = coordinate

	def __repr__(self):
		agree = "no-agr" if self.agree == "" else self.agree
		defin = "no-def" if self.definiteness == "" else self.definiteness
		card = "no-card" if self.cardinality == 0 else self.cardinality
		func = "no-func" if self.head.func == "" else self.head.func
		return str(self.entity) + "/" + str(self.subclass) + ': "' + self.text + '" (' + agree + "/" + defin + "/" + func + "/" + str(card) + ")"


class Sentence:
	def __init__(self, sent_num, start_offset, mood=""):
		self.sent_num = sent_num
		self.start_offset = start_offset
		self.mood = mood

	def __repr__(self):
		mood = "(no mood info)" if self.mood == "" else self.mood
		return "S" + str(self.sent_num) + " from T" + str(self.start_offset + 1) + ", mood: " + mood


def get_descendants(parent, children_dict, seen_tokens, sent_num, conll_tokens):
	my_descendants = []
	my_descendants += children_dict[parent]
	for child in children_dict[parent]:
		if child in seen_tokens:
			sys.stderr.write("\nCycle detected in syntax tree in sentence " + str(sent_num) + " (child of token: '" + conll_tokens[int(parent)].text + "')\n")
			sys.exit("Exiting due to invalid input\n")
		else:
			seen_tokens += [child]
	for child in children_dict[parent]:
		if child in children_dict:
			my_descendants += get_descendants(child, children_dict, seen_tokens, sent_num, conll_tokens)
	return my_descendants
