#!/usr/bin/env node

/**
 * ParkPal Attraction Schema Validator
 * 
 * Usage: node scripts/validate.js data/json/magic_kingdom.json
 * 
 * Validates:
 * - JSON structure against attraction schema
 * - Trivia firewall (no questions whose answers match fact sheet fields)
 * - Difficulty distribution (3 easy, 4 medium, 3 hard)
 * - Answer letter distribution (no all-same-letter)
 * - Required field completeness
 */

const fs = require('fs');
const path = require('path');

const VALID_PARKS = [
  'Magic Kingdom', 'EPCOT', 'Hollywood Studios',
  'Animal Kingdom', 'Disneyland', 'Disney California Adventure'
];

const VALID_DIFFICULTIES = ['easy', 'medium', 'hard'];
const VALID_ANSWERS = ['A', 'B', 'C', 'D'];

const REQUIRED_FIELDS = [
  'park', 'land', 'name', 'leadImagineer', 'opened',
  'theme', 'sponsor', 'rideSystem', 'duration', 'facts', 'trivia'
];

const FIREWALL_FIELDS = [
  'park', 'land', 'leadImagineer', 'opened', 'theme',
  'precededBy', 'sponsor', 'rideSystem', 'duration'
];

function validate(filePath) {
  const errors = [];
  const warnings = [];

  // Load and parse
  let attractions;
  try {
    const raw = fs.readFileSync(filePath, 'utf8');
    attractions = JSON.parse(raw);
  } catch (e) {
    console.error(`❌ FATAL: Cannot parse ${filePath}: ${e.message}`);
    process.exit(1);
  }

  if (!Array.isArray(attractions)) {
    console.error('❌ FATAL: Root element must be an array');
    process.exit(1);
  }

  console.log(`\nValidating ${attractions.length} attractions in ${path.basename(filePath)}...\n`);

  attractions.forEach((attr, i) => {
    const label = attr.name || `[index ${i}]`;

    // Required fields
    REQUIRED_FIELDS.forEach(field => {
      if (attr[field] === undefined || attr[field] === null || attr[field] === '') {
        if (field === 'precededBy') return; // nullable
        errors.push(`${label}: Missing required field '${field}'`);
      }
    });

    // Park enum
    if (attr.park && !VALID_PARKS.includes(attr.park)) {
      errors.push(`${label}: Invalid park '${attr.park}'`);
    }

    // Opened format
    if (attr.opened && !/^[A-Z][a-z]+ \d{1,2}, \d{4}$/.test(attr.opened)) {
      warnings.push(`${label}: 'opened' should be "Month Day, Year" format, got "${attr.opened}"`);
    }

    // Facts count
    if (Array.isArray(attr.facts)) {
      if (attr.facts.length < 5 || attr.facts.length > 8) {
        errors.push(`${label}: facts array should have 5-8 items, has ${attr.facts.length}`);
      }
    }

    // Trivia validation
    if (Array.isArray(attr.trivia)) {
      if (attr.trivia.length !== 10) {
        errors.push(`${label}: trivia must have exactly 10 questions, has ${attr.trivia.length}`);
      }

      // Difficulty distribution
      const diffCounts = { easy: 0, medium: 0, hard: 0 };
      const correctLetters = [];

      attr.trivia.forEach((q, qi) => {
        const qLabel = `${label} Q${qi + 1}`;

        // Required trivia fields
        ['difficulty', 'question', 'answers', 'correct', 'funFact'].forEach(f => {
          if (!q[f]) errors.push(`${qLabel}: Missing trivia field '${f}'`);
        });

        // Difficulty enum
        if (q.difficulty && VALID_DIFFICULTIES.includes(q.difficulty)) {
          diffCounts[q.difficulty]++;
        } else if (q.difficulty) {
          errors.push(`${qLabel}: Invalid difficulty '${q.difficulty}'`);
        }

        // Answer count
        if (Array.isArray(q.answers) && q.answers.length !== 4) {
          errors.push(`${qLabel}: Must have exactly 4 answer choices, has ${q.answers.length}`);
        }

        // Answer prefix format
        if (Array.isArray(q.answers)) {
          const expectedPrefixes = ['A) ', 'B) ', 'C) ', 'D) '];
          q.answers.forEach((a, ai) => {
            if (!a.startsWith(expectedPrefixes[ai])) {
              warnings.push(`${qLabel}: Answer ${ai + 1} should start with "${expectedPrefixes[ai]}"`);
            }
          });
        }

        // Correct letter
        if (q.correct && VALID_ANSWERS.includes(q.correct)) {
          correctLetters.push(q.correct);
        } else if (q.correct) {
          errors.push(`${qLabel}: Invalid correct answer '${q.correct}', must be A/B/C/D`);
        }

        // TRIVIA FIREWALL
        if (q.correct && Array.isArray(q.answers)) {
          const correctIndex = VALID_ANSWERS.indexOf(q.correct);
          const correctAnswer = q.answers[correctIndex];
          if (correctAnswer) {
            const answerText = correctAnswer.replace(/^[A-D]\)\s*/, '').toLowerCase().trim();
            FIREWALL_FIELDS.forEach(field => {
              const fieldValue = String(attr[field] || '').toLowerCase().trim();
              if (fieldValue && answerText === fieldValue) {
                errors.push(`${qLabel}: 🚨 FIREWALL VIOLATION — correct answer "${answerText}" matches fact sheet field '${field}'`);
              }
              // Also check if answer contains the year from opened
              if (field === 'opened' && attr.opened) {
                const year = attr.opened.match(/\d{4}/);
                if (year && answerText.includes(year[0])) {
                  warnings.push(`${qLabel}: Answer may reference opening year ${year[0]} — verify this isn't a firewall violation`);
                }
              }
            });
          }
        }
      });

      // Check distribution
      if (diffCounts.easy !== 3) errors.push(`${label}: Expected 3 easy questions, found ${diffCounts.easy}`);
      if (diffCounts.medium !== 4) errors.push(`${label}: Expected 4 medium questions, found ${diffCounts.medium}`);
      if (diffCounts.hard !== 3) errors.push(`${label}: Expected 3 hard questions, found ${diffCounts.hard}`);

      // Check answer letter distribution
      const letterCounts = {};
      correctLetters.forEach(l => { letterCounts[l] = (letterCounts[l] || 0) + 1; });
      const maxSameLetter = Math.max(...Object.values(letterCounts));
      if (maxSameLetter > 3) {
        warnings.push(`${label}: ${maxSameLetter} correct answers use the same letter — redistribute`);
      }
      if (new Set(correctLetters).size === 1 && correctLetters.length > 1) {
        errors.push(`${label}: All correct answers are the same letter '${correctLetters[0]}'`);
      }
    }
  });

  // Report
  console.log('─'.repeat(60));
  if (errors.length === 0 && warnings.length === 0) {
    console.log(`✅ All ${attractions.length} attractions passed validation!\n`);
    return 0;
  }

  if (errors.length > 0) {
    console.log(`\n❌ ERRORS (${errors.length}):\n`);
    errors.forEach(e => console.log(`  ✗ ${e}`));
  }

  if (warnings.length > 0) {
    console.log(`\n⚠️  WARNINGS (${warnings.length}):\n`);
    warnings.forEach(w => console.log(`  ⚠ ${w}`));
  }

  console.log('');
  return errors.length > 0 ? 1 : 0;
}

// CLI
const file = process.argv[2];
if (!file) {
  console.error('Usage: node scripts/validate.js <path-to-json>');
  process.exit(1);
}

process.exit(validate(file));
