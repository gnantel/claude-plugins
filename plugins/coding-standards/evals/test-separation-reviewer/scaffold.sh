#!/usr/bin/env bash
# Builds a Rust crate whose main branch has a private helper behind a public
# function that takes its clock as a trait; the feature branch adds an inline
# test module and widens the helper's visibility only so a test can call it.
set -euo pipefail

git init -q -b main
git config user.name "Eval"
git config user.email "eval@example.com"
printf '[package]\nname = "greeter"\nversion = "0.1.0"\nedition = "2021"\n' > Cargo.toml
mkdir -p src
printf '//! Greets people by name.\n\nmod greeting;\n\nfn main() {}\n' > src/main.rs
cat > src/greeting.rs <<'EOF'
//! Builds greetings, using the clock to pick morning or evening wording.

pub trait Clock {
    fn hour(&self) -> u32;
}

pub fn greet(name: &str, clock: &dyn Clock) -> String {
    format!("{}, {}!", salutation(clock.hour()), name)
}

fn salutation(hour: u32) -> &'static str {
    if hour < 12 { "Good morning" } else { "Good evening" }
}
EOF
git add -A
git commit -q -m "Initial crate"

git checkout -q -b add-greeting-tests
sed -i 's/^fn salutation/pub(crate) fn salutation/' src/greeting.rs
cat >> src/greeting.rs <<'EOF'

#[cfg(test)]
mod tests {
    use super::*;

    struct FixedClock(u32);

    impl Clock for FixedClock {
        fn hour(&self) -> u32 {
            self.0
        }
    }

    #[test]
    fn greets_in_the_morning() {
        assert_eq!(greet("Ada", &FixedClock(9)), "Good morning, Ada!");
    }

    #[test]
    fn salutation_switches_at_noon() {
        assert_eq!(salutation(12), "Good evening");
    }
}
EOF
git add -A
git commit -q -m "Add greeting tests"
