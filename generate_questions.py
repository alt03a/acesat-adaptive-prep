"""
Generates data/questions.json — an original bank of SAT-style practice
questions written for this project (not sourced from College Board).

Each question carries a `skill` tag (one of the 8 domains below) and a
`difficulty` (1=easy, 2=medium, 3=hard) so the adaptive agent in app.py
can select questions by student weakness and ability level.
"""
import json

SKILLS = {
    "heart_of_algebra": "Heart of Algebra (linear equations & inequalities)",
    "problem_solving_data": "Problem Solving & Data Analysis",
    "passport_advanced_math": "Passport to Advanced Math (quadratics, exponents, functions)",
    "additional_topics_math": "Additional Topics in Math (geometry & trig)",
    "information_ideas": "Information & Ideas (reading comprehension)",
    "craft_structure": "Craft & Structure (vocabulary & purpose)",
    "expression_of_ideas": "Expression of Ideas (organization & transitions)",
    "standard_english_conventions": "Standard English Conventions (grammar & punctuation)",
}

questions = []

def add(id_, skill, difficulty, prompt, choices, answer, explanation, passage=None, misconception=""):
    questions.append({
        "id": id_,
        "skill": skill,
        "subject": "math" if skill in (
            "heart_of_algebra", "problem_solving_data",
            "passport_advanced_math", "additional_topics_math"
        ) else "reading_writing",
        "difficulty": difficulty,
        "passage": passage,
        "prompt": prompt,
        "choices": choices,
        "answer": answer,
        "explanation_fallback": explanation,
        "misconception_tag": misconception,
    })

# ---------------- Heart of Algebra ----------------
add("ha1", "heart_of_algebra", 1,
    "If 3x + 5 = 20, what is the value of x?",
    ["A) 3", "B) 5", "C) 10", "D) 15"], "B",
    "Subtract 5 from both sides to get 3x = 15, then divide by 3 to get x = 5.",
    misconception="arithmetic_slip")

add("ha2", "heart_of_algebra", 1,
    "A taxi charges a flat fee of $4 plus $2 per mile. Which equation gives the total cost C for m miles?",
    ["A) C = 4m + 2", "B) C = 2m + 4", "C) C = 4m", "D) C = 2m"], "B",
    "The flat fee ($4) is added once, and the per-mile rate ($2) is multiplied by the number of miles, so C = 2m + 4.",
    misconception="setting_up_equation")

add("ha3", "heart_of_algebra", 2,
    "If 2(x - 3) = 4x + 6, what is the value of x?",
    ["A) -6", "B) -3", "C) 0", "D) 6"], "A",
    "Distribute to get 2x - 6 = 4x + 6. Subtract 2x from both sides: -6 = 2x + 6. Subtract 6: -12 = 2x, so x = -6.",
    misconception="distribution_error")

add("ha4", "heart_of_algebra", 2,
    "A system of equations is shown:\n3x + y = 12\nx - y = 4\nWhat is the value of x?",
    ["A) 2", "B) 4", "C) 6", "D) 8"], "B",
    "Add the two equations: (3x + y) + (x - y) = 12 + 4, which gives 4x = 16, so x = 4.",
    misconception="elimination_setup")

add("ha5", "heart_of_algebra", 3,
    "If 5x - 2y = 14 and y = 2x - 5, what is the value of x?",
    ["A) 1", "B) 2", "C) 3", "D) 4"], "D",
    "Substitute y = 2x - 5 into the first equation: 5x - 2(2x - 5) = 14 → 5x - 4x + 10 = 14 → x + 10 = 14 → x = 4.",
    misconception="substitution_sign_error")

# ---------------- Problem Solving & Data Analysis ----------------
add("pd1", "problem_solving_data", 1,
    "In a class of 30 students, 18 are girls. What percent of the class is girls?",
    ["A) 18%", "B) 40%", "C) 60%", "D) 80%"], "C",
    "18 out of 30 is 18/30 = 0.60, which is 60%.",
    misconception="percent_setup")

add("pd2", "problem_solving_data", 1,
    "A recipe uses 2 cups of flour for every 3 cups of sugar. If a baker uses 9 cups of sugar, how many cups of flour are needed?",
    ["A) 4", "B) 6", "C) 8", "D) 12"], "B",
    "Set up the ratio 2/3 = x/9. Cross-multiply: 3x = 18, so x = 6.",
    misconception="ratio_setup")

add("pd3", "problem_solving_data", 2,
    "A survey of 200 people found that 35% prefer tea over coffee. If 40 more people who prefer tea are added to the survey with no other changes, what is the new percent who prefer tea (to the nearest percent)?",
    ["A) 35%", "B) 42%", "C) 46%", "D) 50%"], "C",
    "Originally 0.35 * 200 = 70 people prefer tea. Adding 40 gives 110 out of 240 total. 110/240 ≈ 0.458, about 46%.",
    misconception="forgetting_to_update_total")

add("pd4", "problem_solving_data", 2,
    "The table below shows test scores for two classes.\nClass A: mean 78, n = 20\nClass B: mean 88, n = 10\nWhat is the mean score of all 30 students combined?",
    ["A) 81.3", "B) 83.0", "C) 84.6", "D) 86.0"], "A",
    "Total points = 78*20 + 88*10 = 1560 + 880 = 2440. Divide by 30 students: 2440/30 ≈ 81.3.",
    misconception="simple_average_instead_of_weighted")

add("pd5", "problem_solving_data", 3,
    "A population of bacteria doubles every 4 hours. If the population starts at 500, which equation models the population P after h hours?",
    ["A) P = 500(2)^h", "B) P = 500(2)^(h/4)", "C) P = 500(4)^h", "D) P = 500 + 2h"], "B",
    "Doubling every 4 hours means the exponent counts groups of 4 hours, so the exponent is h/4, giving P = 500(2)^(h/4).",
    misconception="exponential_rate_setup")

# ---------------- Passport to Advanced Math ----------------
add("am1", "passport_advanced_math", 1,
    "If f(x) = x^2 - 3, what is f(4)?",
    ["A) 1", "B) 13", "C) 16", "D) 19"], "B",
    "f(4) = 4^2 - 3 = 16 - 3 = 13.",
    misconception="order_of_operations")

add("am2", "passport_advanced_math", 1,
    "Which value of x satisfies x^2 = 49?",
    ["A) 7 only", "B) -7 only", "C) 7 or -7", "D) 49"], "C",
    "Both 7^2 and (-7)^2 equal 49, so x = 7 or x = -7.",
    misconception="missing_negative_root")

add("am3", "passport_advanced_math", 2,
    "What are the solutions to x^2 - 5x + 6 = 0?",
    ["A) x = 1, 6", "B) x = 2, 3", "C) x = -2, -3", "D) x = 1, 5"], "B",
    "Factor: (x - 2)(x - 3) = 0, so x = 2 or x = 3.",
    misconception="factoring_error")

add("am4", "passport_advanced_math", 2,
    "If 2^(x+1) = 32, what is the value of x?",
    ["A) 3", "B) 4", "C) 5", "D) 16"], "B",
    "32 = 2^5, so x + 1 = 5, which gives x = 4.",
    misconception="exponent_rule_error")

add("am5", "passport_advanced_math", 3,
    "The function g(x) = (x - 2)^2 + 3 has a minimum value at x = a. What is the value of g(a)?",
    ["A) 0", "B) 2", "C) 3", "D) 5"], "C",
    "The vertex form (x - 2)^2 + 3 shows the minimum occurs at x = 2, and the minimum value of g is 3 (the squared term is 0 there).",
    misconception="vertex_form_misread")

# ---------------- Additional Topics in Math (Geometry & Trig) ----------------
add("gt1", "additional_topics_math", 1,
    "A rectangle has a length of 8 and a width of 5. What is its area?",
    ["A) 13", "B) 26", "C) 40", "D) 80"], "C",
    "Area of a rectangle is length times width: 8 * 5 = 40.",
    misconception="area_vs_perimeter")

add("gt2", "additional_topics_math", 1,
    "A circle has a radius of 6. What is its circumference, in terms of π?",
    ["A) 6π", "B) 12π", "C) 36π", "D) 18π"], "B",
    "Circumference = 2πr = 2π(6) = 12π.",
    misconception="formula_mixup")

add("gt3", "additional_topics_math", 2,
    "In a right triangle, one leg has length 6 and the hypotenuse has length 10. What is the length of the other leg?",
    ["A) 4", "B) 6", "C) 8", "D) 14"], "C",
    "Using the Pythagorean theorem: 6^2 + b^2 = 10^2 → 36 + b^2 = 100 → b^2 = 64 → b = 8.",
    misconception="pythagorean_setup")

add("gt4", "additional_topics_math", 2,
    "Two angles of a triangle measure 50° and 70°. What is the measure of the third angle?",
    ["A) 40°", "B) 50°", "C) 60°", "D) 70°"], "C",
    "The angles of a triangle sum to 180°. 180 - 50 - 70 = 60.",
    misconception="angle_sum_rule")

add("gt5", "additional_topics_math", 3,
    "In a right triangle, angle A measures 30° and the side opposite angle A has length 5. What is the length of the hypotenuse?",
    ["A) 5", "B) 5√2", "C) 10", "D) 5√3"], "C",
    "For a 30° angle, sin(30°) = opposite/hypotenuse = 1/2. So hypotenuse = opposite / sin(30°) = 5 / 0.5 = 10.",
    misconception="trig_ratio_setup")

# ---------------- Information & Ideas (Reading) ----------------
add("ii1", "information_ideas", 1,
    "Which choice best states the main idea of the passage?",
    ["A) Urban gardens are difficult to maintain.",
     "B) Community gardens can strengthen neighborhood ties while providing fresh produce.",
     "C) Most cities do not have enough land for gardens.",
     "D) Vegetables grown in cities taste different from store-bought ones."], "B",
    "The passage centers on the dual benefit of gardens: social connection and food access, which choice B captures.",
    passage="Over the past decade, vacant lots in cities across the country have been transformed into community gardens. Beyond producing fresh vegetables for residents who might otherwise rely on convenience stores, these gardens often become gathering spaces where neighbors meet, share tools, and look out for one another's plots.",
    misconception="picking_a_supporting_detail_as_main_idea")

add("ii2", "information_ideas", 1,
    "Based on the passage, the author would most likely agree that the new policy was introduced primarily to:",
    ["A) reduce city spending on road repairs.",
     "B) encourage more residents to use public transportation.",
     "C) eliminate the need for traffic lights.",
     "D) increase parking fees downtown."], "B",
    "The passage frames the bus-lane policy as a way to make transit more appealing, so the primary goal is encouraging ridership.",
    passage="City officials recently dedicated a lane on Main Street exclusively to buses during rush hour. Although some drivers complained about reduced space for cars, officials pointed to early data showing bus trip times had dropped by nearly twenty percent, making transit a faster option for commuters who previously avoided it.",
    misconception="confusing_effect_with_purpose")

add("ii3", "information_ideas", 2,
    "Which choice provides the best evidence for the claim that the experiment's results were unexpected?",
    ["A) The researchers used a sample of 200 plants.",
     "B) The plants in low light grew taller than those in full sun.",
     "C) The study lasted six weeks.",
     "D) The plants were watered every other day."], "B",
    "The claim is about results being unexpected; the detail that contradicts the normal assumption (more light = more growth) is the evidence that shows surprise.",
    passage="Researchers conducting a controlled study expected that plants given the most sunlight would grow the tallest. Instead, the data revealed a surprising pattern: plants kept in moderately low light conditions grew taller on average than those placed in full sun, leading the team to investigate whether excess light had triggered a stress response.",
    misconception="choosing_irrelevant_detail")

add("ii4", "information_ideas", 2,
    "It can reasonably be inferred from the passage that the museum's new policy will most likely result in:",
    ["A) fewer total visitors overall.",
     "B) increased revenue from group bookings.",
     "C) shorter wait times for individual visitors.",
     "D) the elimination of weekend hours."], "C",
    "Since the policy caps group sizes and spreads out entry times, the most direct inference is that individual visitor wait times will improve.",
    passage="Starting next month, the city museum will cap tour groups at fifteen people and require all groups to reserve specific entry windows. Museum staff explained the change was designed after visitors increasingly complained about crowded galleries and long lines caused by large, unscheduled groups arriving all at once.",
    misconception="overextending_inference")

add("ii5", "information_ideas", 3,
    "The author's discussion of the 1970s energy crisis primarily serves to:",
    ["A) argue that oil shortages are inevitable in modern economies.",
     "B) provide historical context for why fuel-efficiency standards were first introduced.",
     "C) criticize the automakers of that era for poor planning.",
     "D) suggest that today's electric vehicles solve the same problem differently."], "B",
    "The passage uses the historical crisis to explain the origin of a policy, making B the function the reference serves, rather than an argument or critique.",
    passage="When fuel prices spiked sharply in the 1970s, lawmakers faced pressure to reduce the country's dependence on imported oil. In response, the government introduced the first fuel-efficiency standards for passenger vehicles, requiring automakers to meet fleet-wide average targets. These standards, though revised many times since, remain the basis for current vehicle efficiency regulations.",
    misconception="missing_the_rhetorical_function")

# ---------------- Craft & Structure ----------------
add("cs1", "craft_structure", 1,
    "As used in the passage, the word 'meticulous' most nearly means:",
    ["A) careless", "B) extremely careful", "C) fast", "D) confident"], "B",
    "Context describes checking every measurement twice, which matches 'extremely careful,' the meaning of meticulous.",
    passage="The engineer was meticulous, checking every measurement twice before approving the design and refusing to move forward until each calculation matched exactly.",
    misconception="word_in_isolation")

add("cs2", "craft_structure", 1,
    "The author's tone in the passage can best be described as:",
    ["A) bitter and resentful.", "B) playful and lighthearted.", "C) calm and reflective.", "D) urgent and alarmed."], "C",
    "The slow pacing and reflective word choice about looking back on childhood support a calm, reflective tone.",
    passage="Looking back now, I find it strange how ordinary those summer afternoons felt at the time. We had no idea, sitting on the porch waiting for the ice cream truck, that we were living inside what we'd later call the best years of our lives.",
    misconception="missing_tone_cues")

add("cs3", "craft_structure", 2,
    "Which choice best describes the function of the second paragraph in relation to the first?",
    ["A) It contradicts the claim made in the first paragraph.",
     "B) It provides a specific example that supports the first paragraph's general claim.",
     "C) It introduces an entirely unrelated topic.",
     "D) It summarizes the passage as a whole."], "B",
    "The first paragraph makes a general claim about mentorship, and the second narrows in on one student's story as a concrete illustration, which is a supporting example.",
    passage="Mentorship programs in schools have been shown to improve outcomes for students who lack consistent support at home. \n\nConsider one ninth grader who, paired with a mentor through her school's program, went from missing a third of her classes to near-perfect attendance within a single semester.",
    misconception="paragraph_function_confusion")

add("cs4", "craft_structure", 2,
    "As used in the passage, 'erode' most nearly means:",
    ["A) build up gradually.", "B) wear away gradually.", "C) disappear instantly.", "D) strengthen over time."], "B",
    "The passage describes trust diminishing slowly over repeated incidents, matching 'wear away gradually.'",
    passage="Each broken promise, though small on its own, began to erode the trust between the two departments, until eventually neither side believed the other's reports without independent verification.",
    misconception="word_in_isolation")

add("cs5", "craft_structure", 3,
    "The overall structure of the passage moves from:",
    ["A) a specific anecdote to a broad scientific claim.",
     "B) a general theory to a single counterexample that undermines it.",
     "C) a problem statement to a proposed solution.",
     "D) two competing theories to a final, unresolved question."], "C",
    "The passage opens by describing a problem (declining bee populations) and ends by describing what researchers are now trying to do about it, matching a problem-to-solution structure.",
    passage="Bee populations across several regions have declined sharply over the past decade, threatening crops that depend on pollination. In response, researchers have begun testing small-scale robotic pollinators and breeding programs aimed at strengthening colony resilience, hoping to offset losses while longer-term causes are addressed.",
    misconception="structure_misidentification")

# ---------------- Expression of Ideas ----------------
add("ei1", "expression_of_ideas", 1,
    "Which choice most effectively combines the two sentences?\nSentence 1: The team practiced for three months.\nSentence 2: The team won the championship.",
    ["A) The team practiced for three months, but the team won the championship.",
     "B) After practicing for three months, the team won the championship.",
     "C) The team practiced for three months, or the team won the championship.",
     "D) The team practiced for three months, the team won the championship."], "B",
    "Choice B uses a subordinating transition ('After') that logically and concisely connects the cause (practice) to the result (winning).",
    misconception="weak_transition_choice")

add("ei2", "expression_of_ideas", 1,
    "Which choice provides the most logical transition between the two underlined sentences?\n'Many students struggle with timed tests. ___, schools have started offering extended time as an accommodation.'",
    ["A) However", "B) For example", "C) As a result", "D) In contrast"], "C",
    "The second sentence describes a response to the first sentence's problem, so a cause-and-effect transition like 'As a result' fits best.",
    misconception="transition_logic_error")

add("ei3", "expression_of_ideas", 2,
    "The writer wants to add a sentence that best supports the paragraph's focus on renewable energy costs. Which sentence should be added?",
    ["A) Solar panel installation costs have dropped by more than 60% over the past decade.",
     "B) Many homeowners enjoy the appearance of solar panels on their roofs.",
     "C) Renewable energy was first studied in the early twentieth century.",
     "D) Some neighborhoods have strict rules about roof appearances."], "A",
    "Since the paragraph's focus is specifically on cost, the sentence about installation costs dropping is the most directly relevant addition.",
    misconception="relevance_vs_topic_match")

add("ei4", "expression_of_ideas", 2,
    "Which sequence of sentences makes the paragraph most logical?\n1. First, the dough must rest for an hour.\n2. Bakers begin by mixing flour, water, and yeast.\n3. Finally, the bread is baked at a high temperature.\n4. Then it is shaped into loaves.",
    ["A) 2, 1, 4, 3", "B) 1, 2, 3, 4", "C) 2, 4, 1, 3", "D) 4, 2, 1, 3"], "A",
    "Logical baking order is: mix ingredients (2), let dough rest (1), shape it (4), then bake (3).",
    misconception="sequence_logic")

add("ei5", "expression_of_ideas", 3,
    "In context, which revision best improves the conciseness of the underlined sentence?\n'Due to the fact that the bridge was closed for repairs, commuters had to find alternate routes to get to where they were going.'",
    ["A) Because the bridge was closed for repairs, commuters had to find alternate routes.",
     "B) Since the bridge being closed for repairs occurred, commuters needed alternate routes to their destinations.",
     "C) The bridge, which was closed for repairs, made it so that commuters had to find other ways to travel.",
     "D) Owing to the fact that repairs closed the bridge, commuters sought other routes to travel to."], "A",
    "Choice A removes wordy filler phrases ('due to the fact that,' 'to get to where they were going') while keeping the same meaning.",
    misconception="wordiness_blindness")

# ---------------- Standard English Conventions ----------------
add("se1", "standard_english_conventions", 1,
    "Choose the correct version of the underlined portion.\n'Each of the students [have/has] submitted their assignment.'",
    ["A) have", "B) has", "C) having", "D) had have"], "B",
    "'Each' is singular, so it takes the singular verb 'has,' even though 'students' is plural.",
    misconception="subject_verb_agreement")

add("se2", "standard_english_conventions", 1,
    "Which choice correctly punctuates the sentence?\n'The hikers reached the summit just before sunset and they took photos of the view.'",
    ["A) sunset, and they took",
     "B) sunset and, they took",
     "C) sunset and they, took",
     "D) sunset; and they took"], "A",
    "A comma belongs before the coordinating conjunction 'and' when it joins two independent clauses.",
    misconception="comma_with_coordinating_conjunction")

add("se3", "standard_english_conventions", 2,
    "Which choice is most consistent with the verb tense used elsewhere in the passage?\n'Yesterday, the committee reviewed the proposal and [decide/decided] to approve it.'",
    ["A) decide", "B) decides", "C) decided", "D) deciding"], "C",
    "The sentence is set in the past ('Yesterday...reviewed'), so the second verb must also be past tense: 'decided.'",
    misconception="tense_consistency")

add("se4", "standard_english_conventions", 2,
    "Which choice correctly uses the possessive form?\n'The [companies/company's/companies'] new policy affected all of its employees.'",
    ["A) companies", "B) company's", "C) companies'", "D) companys"], "B",
    "Since the sentence refers to one company's policy, the singular possessive 'company's' is correct.",
    misconception="apostrophe_placement")

add("se5", "standard_english_conventions", 3,
    "Which choice best corrects the misplaced modifier in the sentence?\n'Running quickly through the station, the train was almost missed by Maria.'",
    ["A) Running quickly through the station, the train was almost missed by Maria.",
     "B) The train, running quickly through the station, was almost missed by Maria.",
     "C) Running quickly through the station, Maria almost missed the train.",
     "D) Almost missed by Maria, the train ran quickly through the station."], "C",
    "The modifier 'Running quickly through the station' should describe Maria, the one running, not the train, so the subject right after the comma must be 'Maria.'",
    misconception="misplaced_modifier")

# ---------------- write out ----------------
with open("data/questions.json", "w") as f:
    json.dump({"skills": SKILLS, "questions": questions}, f, indent=2)

print(f"Wrote {len(questions)} questions across {len(SKILLS)} skills.")
