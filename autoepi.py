# autoepistemic_logic_solver.py
##Incomplete implementations !!
class Proposition:
    """Represents a simple proposition or fact."""
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


class Belief:
    """Represents a belief in a proposition with support tracking."""
    def __init__(self, proposition, support=1, negated=False):
        self.proposition = proposition
        self.support = support  # Numeric support level, defaulting to 1
        self.negated = negated  # Indicates if this is a non-belief

    def __repr__(self):
        if self.negated:
            return f"~L({self.proposition}) [Support: {self.support}]"
        else:
            return f"L({self.proposition}) [Support: {self.support}]"

    def increase_support(self, amount=1):
        """Increase the support level of the belief."""
        self.support += amount

    def decrease_support(self, amount=1):
        """Decrease the support level of the belief."""
        self.support -= amount
        if self.support < 0:
            self.support = 0  # Support can't be negative

    def toggle_negation(self):
        """Toggle the belief as a negated or non-belief state."""
        self.negated = not self.negated


class KnowledgeBase:
    """A knowledge base containing beliefs and propositions."""
    def __init__(self):
        self.beliefs = {}

    def add_belief(self, belief):
        """Add or update a belief in the knowledge base."""
        if belief.proposition.name in self.beliefs:
            existing_belief = self.beliefs[belief.proposition.name]
            if belief.negated == existing_belief.negated:
                existing_belief.increase_support(belief.support)
            else:
                existing_belief.decrease_support(belief.support)
        else:
            self.beliefs[belief.proposition.name] = belief

    def find_belief(self, proposition_name):
        """Find a belief by proposition name."""
        return self.beliefs.get(proposition_name, None)

    def unresolved_beliefs(self):
        """Return beliefs that need more information to resolve."""
        return [belief for belief in self.beliefs.values() if belief.support == 0]

    def __repr__(self):
        return "\n".join(str(belief) for belief in self.beliefs.values())


def apply_negation_as_nonbelief(kb):
    """Negates beliefs to reflect non-belief (absence of belief)."""
    for belief in kb.beliefs.values():
        if belief.negated:
            belief.decrease_support()
        else:
            belief.increase_support()


def apply_support_reinforcement(kb, target_belief_name, support_reasons):
    """Reinforce support for a belief based on supporting reasons."""
    belief = kb.find_belief(target_belief_name)
    if belief:
        for reason in support_reasons:
            kb.add_belief(Belief(reason))
            belief.increase_support()


def infer_most_likely_cause(kb):
    """Run inference to prioritize beliefs with stronger support levels."""
    apply_negation_as_nonbelief(kb)

    strongest_belief = max(
        (b for b in kb.beliefs.values() if not b.negated),
        key=lambda b: b.support,
        default=None
    )

    if strongest_belief and strongest_belief.support > 0:
        kb.add_belief(Belief(Proposition(f"Most likely cause: {strongest_belief.proposition.name}")))
        return strongest_belief
    else:
        unresolved = kb.unresolved_beliefs()
        if unresolved:
            return "More depth or information required to conclude."
        return None


# Usage Example
if __name__ == "__main__":
    # Define propositions for each diagnosis
    s_c = Proposition("Cyclophosphamide-induced hemorrhagic cystitis")
    s_m = Proposition("Methotrexate-induced renal toxicity")
    s_r = Proposition("Rituximab unlikely to cause symptoms")
    s_cp = Proposition("Cytarabine and prednisone unlikely to cause symptoms")

    # Initialize knowledge base with some beliefs and negations
    kb = KnowledgeBase()
    kb.add_belief(Belief(s_c))
    kb.add_belief(Belief(s_m))
    kb.add_belief(Belief(s_r, negated=True))  # Non-belief in rituximab as cause
    kb.add_belief(Belief(s_cp, negated=True))  # Non-belief in cytarabine/prednisone as cause

    # Define supporting reasons for cyclophosphamide belief
    support_reasons = [
        Proposition("Consistent with hemorrhagic cystitis symptoms"),
        Proposition("Patient history includes cyclophosphamide use")
    ]

    # Apply support reinforcement for cyclophosphamide belief
    apply_support_reinforcement(kb, "Cyclophosphamide-induced hemorrhagic cystitis", support_reasons)

    # Run inference to find the most likely cause
    most_likely = infer_most_likely_cause(kb)

    # Output the knowledge base
    print("Final Knowledge Base:")
    print(kb)
    print("\nInference Result:")
    print(most_likely)
