from xrenner_marker import *
from xrenner_compatible import *
from xrenner_propagate import *
"""
xrenner - eXternally configurable REference and Non Named Entity Recognizer
modules/xrenner_coref.py
Coreference resolution module. Iterates through markables to find possible matches based on rules.
Author: Amir Zeldes
"""


def find_antecedent(markable, previous_markables, lex, restrict_rule=""):
	"""
	Search for antecedents by cycling through coref rules for previous markables
	:param markable: Markable object to find an antecedent for
	:param previous_markables: Markables in all sentences up to and including current sentence
	:param lex: the LexData object with gazetteer information and model settings
	:param restrict_rule: a string specifying a subset of rules that should be checked (e.g. only rules with 'appos')
	:return: candidate, matching_rule - the best antecedent and the rule that matched it
	"""
	candidate = None
	matching_rule = None
	for rule in lex.coref_rules:
		if candidate is None:
			# If this call of find_antecedent is limited to certain rules, check that the restriction is in the rule
			if restrict_rule == "" or restrict_rule in rule[0]:
				if coref_rule_applies(lex, rule[0], markable):
					candidate = search_prev_markables(markable, previous_markables, rule[1], lex, int(rule[2]), rule[3])
					if candidate is not None:
						matching_rule = rule

	return candidate, matching_rule


def search_prev_markables(markable, previous_markables, rule, lex, max_dist, propagate):
	"""
	Search for antecedent to specified markable using a specified rule
	:param markable: The markable object to find an antecedent for
	:param previous_markables: The list of know markables up to and including the current sentence;
								markables beyond current markable but in its sentence are included for cataphora.
	:param rule: The antecedent specification part of the coref rule being checked
	:param lex: the LexData object with gazetteer information and model settings
	:param max_dist: Maximum distance in sentences for the antecedent search (0 for search within sentence)
	:param propagate: Whether to progpagate features upon match and in which direction
	:return: the selected candidate Markable object
	"""
	candidate_list = []
	if rule.find("lookahead") > -1:
		referents_to_loop = previous_markables
	else:
		referents_to_loop = reversed(previous_markables)
	for candidate in referents_to_loop:  # loop through previous markables backwards
		#DEBUG breakpoint:
		if markable.text.strip() == lex.debug["ana"]:
			pass
			if candidate.text.strip() == lex.debug["ante"]:
				pass
		if markable.sentence.sent_num - candidate.sentence.sent_num <= max_dist:
			if ((int(markable.head.id) > int(candidate.head.id) and
			rule.find("lookahead") == -1) or (int(markable.head.id) < int(candidate.head.id) and rule.find("lookahead") > -1)):
				if candidate.group not in markable.non_antecdent_groups:
					if coref_rule_applies(lex, rule, candidate, markable):
						if not markables_overlap(markable, candidate):
							if markable.form == "pronoun":
								if agree_compatible(markable, candidate, lex) or (rule.find("anyagree") > -1 and group_agree_compatible(markable,candidate,previous_markables,lex)):
									if entities_compatible(markable, candidate, lex) and cardinality_compatible(markable, candidate, lex):
										candidate_list.append(candidate)
							elif markable.text.strip() == candidate.text.strip() or (len(markable.text) > 4 and (candidate.text.lower() == markable.text.lower())):
								propagate_entity(markable, candidate, propagate)
								return candidate
							elif markable.text.strip() + "|" + candidate.text.strip() in lex.coref and entities_compatible(
									markable, candidate, lex) and agree_compatible(markable, candidate, lex):
								markable.coref_type = lex.coref[markable.text.strip() + "|" + candidate.text.strip()]
								propagate_entity(markable, candidate)
								return candidate
							elif markable.entity == candidate.entity and agree_compatible(markable, candidate, lex) and (markable.head.text == candidate.head.text or
							(len(markable.head.text) > 3 and (candidate.head.text.lower() == markable.head.text.lower())) or
							(markable.core_text.count(" ") > 2 and (markable.core_text.lower() == candidate.core_text.lower())) or
							(markable.head.lemma == candidate.head.lemma and lex.filters["lemma_match_pos"].match(markable.head.pos) is not None
							and lex.filters["lemma_match_pos"].match(candidate.head.pos) is not None)):
								if modifiers_compatible(markable, candidate, lex) and modifiers_compatible(candidate, markable, lex):
									if propagate.startswith("propagate"):
										propagate_entity(markable, candidate, propagate)
									return candidate
							elif markable.entity == candidate.entity and (isa(markable, candidate, lex) or isa(candidate, markable, lex)):
								if modifiers_compatible(markable, candidate, lex, False) and modifiers_compatible(candidate, markable, lex, False):
									if propagate.startswith("propagate"):
										propagate_entity(markable, candidate, propagate)
									return candidate
							elif (markable.head.text == candidate.head.text and agree_compatible(markable,candidate,lex) or (markable.head.lemma == candidate.head.lemma and
							lex.filters["lemma_match_pos"].match(markable.head.pos) is not None and lex.filters["lemma_match_pos"].match(candidate.head.pos) is not None)):
								if merge_entities(markable, candidate, previous_markables, lex):
									if propagate.startswith("propagate"):
										propagate_entity(markable, candidate, propagate)
									return candidate
							elif entities_compatible(markable, candidate, lex) and (isa(markable, candidate, lex) or isa(candidate, markable, lex)):
									if modifiers_compatible(markable, candidate, lex) and modifiers_compatible(candidate, markable, lex):
										if merge_entities(markable, candidate, previous_markables, lex):
											if propagate.startswith("propagate"):
												propagate_entity(markable, candidate, propagate)
											return candidate
							elif lex.filters["match_acronyms"] and markable.head.text.isupper() or candidate.head.text.isupper():
								if acronym_match(markable, candidate, lex) or acronym_match(candidate, markable, lex):
									if modifiers_compatible(markable, candidate, lex) and modifiers_compatible(candidate, markable, lex):
										if merge_entities(markable, candidate, previous_markables, lex):
											propagate_entity(markable, candidate, "propagate")
											return candidate
							if rule.find("anytext") > -1:
								if (rule.find("anyagree") > -1 and group_agree_compatible(markable,candidate,previous_markables,lex)) or agree_compatible(markable, candidate, lex):
									if (rule.find("anycardinality") > -1 or cardinality_compatible(markable,candidate,lex)):
										if (rule.find("anyentity") > -1 or entities_compatible(markable,candidate,lex)):
											if propagate.startswith("propagate"):
												propagate_entity(markable, candidate, propagate)
											return candidate
		elif rule.find("lookahead") == -1:
			# Reached back too far according to max_dist, stop looking
			break
	if len(candidate_list)>0:
		candidates_to_remove = []
		for candidate_item in candidate_list:
			# Remove items that are prohibited by entity agree mapping
			agree_entity_mapping = lex.filters["agree_entity_mapping"].split(";")
			for pair in agree_entity_mapping:
				if pair.split(">")[0] == markable.agree and pair.split(">")[1] != candidate_item.entity:
					candidates_to_remove.append(candidate_item)
		for removal in candidates_to_remove:
			candidate_list.remove(removal)
		if len(candidate_list)>0:
			return best_candidate(markable, candidate_list, lex)
		else:
			return None
	else:
		return None


def coref_rule_applies(lex, rule, mark, anaphor=None):
	"""
	Check whether a markable definition from a coref rule applies to this markable
	:param lex: the LexData object with gazetteer information and model settings
	:param rule: the constraints defining the relevant Markable
	:param mark: the Markable object to check constraints against
	:param anaphor: if this is an antecedent check, the anaphor is passed for $1-style constraint checks
	:return: Boolean: True if 'mark' fits all constraints, False if any of them fail
	"""
	if rule is None or rule == "none":
		return True
	constraints = rule.split("&")
	for constraint in constraints:
		group_failure = False
		negative = False
		if constraint.endswith("*"):
			group_failure = True
			constraint = constraint[0:-1]
		if "=" in constraint:
			key = constraint.split("=")[0]
			value = constraint.split("=")[1]
			if key[-1] == "!":
				negative = True
				key = key[0:-1]
			if value.startswith("/") and value.endswith("/"):
				value = value[1:-1]
			elif value == "True" or value == "False":
				pass
			elif value.startswith("$") and anaphor is not None:
				if key in ["form", "text", "agree", "entity", "subclass", "cardinality"]:
					value = "^" + re.escape(str(getattr(anaphor, key)).strip()) + "$"
				elif key == "text_lower":
					value = "^" + re.escape(getattr(anaphor, "text").lower()) + "$"
				elif key in ["func", "pos", "lemma"]:
					value = "^" + re.escape(getattr(anaphor.head, key)) + "$"
				elif key == "mod":
					mods = getattr(anaphor.head, "modifiers")
					found_mod = False
					for mod1 in mark.head.modifiers:
						for mod2 in mods:
							if mod1.lemma == mod2.lemma and lex.filters["det_func"].match(mod1.func) is None and \
							lex.filters["det_func"].match(mod2.func) is None:
								found_mod = True
					if not found_mod:
						if group_failure and anaphor is not None:
							mark.non_antecdent_groups.add(anaphor.group)
						return False
					else:
						rule_property = "$1"
						key = ""
			if key == "text_lower":
				value = value.lower()
			value_matcher = re.compile(value)
			if key in ["form", "text", "agree", "entity", "subclass", "cardinality"]:
				rule_property = str(getattr(mark, key)).strip()
			elif key == "text_lower":
				rule_property = getattr(mark, "text").lower().strip()
			elif key in ["func", "pos", "lemma"]:
				rule_property = getattr(mark.head, key)
			elif key == "quoted":
				rule_property = str(getattr(mark.head, "quoted"))
			elif key == "mood":
				rule_property = mark.sentence.mood
			elif key == "has_child_func":
				rule_property = ""
				for func in mark.head.child_funcs:
					rule_property += func + ";"
			elif key == "head":
				if "$" in value:
					if not mark.head.head == anaphor.head.id:
						if group_failure and anaphor is not None:
							anaphor.non_antecdent_groups.add(mark.group)
						return False
					rule_property = "$1"
				else:
					if re.match(value, mark.head.head) is None:
						if group_failure and anaphor is not None:
							anaphor.non_antecdent_groups.add(mark.group)
						return False
			elif key == "child":
				if "$" in value:
					if not anaphor.head.head == mark.head.id:
						if group_failure and mark is not None:
							mark.non_antecdent_groups.add(anaphor.group)
						return False
					rule_property = "$1"
				else:
					if re.match(value, anaphor.head.head) is None:
						if group_failure and mark is not None:
							mark.non_antecdent_groups.add(anaphor.group)
						return False
			elif re.match(r"last\[([^\[]+)\]", key) is not None:
				match = re.match(r"last\[([^\[]+)\]", key)
				agree = match.group(1)
				if agree in lex.last:
					rule_property = lex.last[agree].entity
				else:
					rule_property = ""
			elif "$" not in rule_property:
				rule_property = ""

			if rule_property is None:
				rule_property = ""

			if (value_matcher.search(rule_property) is None and negative is False) and "$1" not in rule_property:
				if group_failure and anaphor is not None:
					anaphor.non_antecdent_groups.add(mark.group)
				return False
			elif (value_matcher.search(rule_property) is not None and negative is True) and "$1" not in rule_property:
				if group_failure and anaphor is not None:
					anaphor.non_antecdent_groups.add(mark.group)
				return False
		elif constraint == "sameparent":
			if mark.head.head == anaphor.head.head and not mark.head.head == '0':
				return True
			else:
				if group_failure and anaphor is not None:
					anaphor.non_antecdent_groups.add(mark.group)
				return False
		elif constraint == "!sameparent":
			if mark.head.head == anaphor.head.head and not mark.head.head == '0':
				if group_failure and anaphor is not None:
					anaphor.non_antecdent_groups.add(mark.group)
				return False
			else:
				return True
	return True


def antecedent_prohibited(markable, conll_tokens, lex):
	"""
	Check whether a Markable object is prohibited from having an antecedent
	:param markable: The Markable object to check
	:param conll_tokens: The list of ParsedToken objects up to and including the current sentence
	:param lex: the LexData object with gazetteer information and model settings
	:return: Boolean
	"""
	mismatch = True
	if "/" in lex.filters["no_antecedent"]:
		constraints = lex.filters["no_antecedent"].split(";")
		for constraint in constraints:
			if not mismatch:
				return True
			descriptions = constraint.split("&")
			mismatch = False
			for token_description in descriptions:
				if token_description.startswith("^"):
					test_token = conll_tokens[markable.start]
				elif token_description.startswith("$"):
					test_token = conll_tokens[markable.end]
				elif token_description.startswith("@"):
					test_token = markable.head
				else:
					# Invalid token description
					return False
				token_description = token_description[1:]
				pos, word = token_description.split("/")
				if pos.startswith("!"):
					pos = pos[1:]
					negative_pos = True
				else:
					negative_pos = False
				if word.startswith("!"):
					word = word[1:]
					negative_word = True
				else:
					negative_word = False
				pos_matcher = re.compile(pos)
				word_matcher = re.compile(word)
				if (pos_matcher.match(test_token.pos) is None and not negative_pos) or (pos_matcher.match(test_token.pos) is not None and negative_pos) or \
				(word_matcher.match(test_token.text.strip()) is None and not negative_word) or (word_matcher.match(test_token.text.strip()) is not None and negative_word):
					mismatch = True
					break
	if mismatch:
		return False
	else:
		return True



