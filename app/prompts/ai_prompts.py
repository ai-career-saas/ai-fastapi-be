INTERVIEW_GEN_PROMPT = """You are a senior interview coach. Generate interview questions.
Target role: {target_role}
Experience level: {experience_level}
Job description: {job_description}
Resume: {resume_text}

Generate 8-10 diverse interview questions:
- 3-4 technical questions specific to the role
- 2-3 behavioral (STAR method expected)
- 1-2 situational / problem-solving
- 1 culture fit

For each question provide:
- category: technical|behavioral|situational|culture_fit
- difficulty: easy|medium|hard
- why_asked: Thai explanation (1-2 sentences) ว่า interviewer ถามเพื่ออะไร
- key_points: list of 2-3 points the candidate should cover
- sample_answer_tip: Thai tip on how to answer well
- follow_up: optional follow-up question

Also provide:
- preparation_tips: 3-5 Thai tips for this specific role
- overall_advice: Thai paragraph of overall interview advice"""


ATS_SCORE_PROMPT = """You are an ATS (Applicant Tracking System) scanner expert.
Analyze this resume against the job description.

Resume:
{resume_text}

Job Description:
{job_description}

Tasks:
1. Extract ALL requirements/keywords from job description (skills, tools, qualifications, soft skills)
2. Check each keyword: found=true if exact or very close match exists in resume
3. Calculate:
   - keyword_match_rate = matched_keywords / total_keywords * 100 (round to int)
   - overall_score = weighted score (critical keywords weight 3x, important 2x, nice-to-have 1x)
   - grade: 90+ = A+, 80-89 = A, 70-79 = B+, 60-69 = B, 50-59 = C+, 40-49 = C, 30-39 = D, <30 = F
4. Evaluate sections: contact_info, summary/objective, work_experience, skills, education, formatting
5. Check formatting issues: tables/graphics ATS cannot read, missing sections, inconsistent dates, etc
6. estimated_pass_rate: "สูง" if score>=70, "ปานกลาง" if 50-69, "ต่ำ" if <50

All feedback/summary/suggestions must be in Thai."""
