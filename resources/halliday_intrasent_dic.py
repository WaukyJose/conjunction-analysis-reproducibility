# ------------------------- INTRA-CLAUSE CONJUNCTIONS -------------------------
INTRA_CLAUSE_CONJUNCTIONS = {
    "Enhancement": {
        "Temporal": {
            "Simultaneous": {
                "paratactic": [
                    "and",
                    "meanwhile",
                    "at the same time",
                    "simultaneously",
                    "just then",
                ],
                "hypotactic": ["while", "as", "when", "whilst", "just as"],
            },
            "Later": {
                "paratactic": [
                    "then",
                    "afterwards",
                    "subsequently",
                    "later on",
                    "next",
                ],
                "hypotactic": ["after", "since", "once", "when", "as soon as"],
            },
            "Earlier": {
                "paratactic": [
                    "before that",
                    "previously",
                    "earlier",
                    "until then",
                    "hitherto",
                ],
                "hypotactic": ["before", "until", "till", "prior to", "by the time"],
            },
            "Conclusive": {
                "paratactic": ["finally", "in the end", "last of all"],
                "hypotactic": [],
            },
        },
        "Causal-Conditional": {
            "Reason": {
                "paratactic": [
                    "so",
                    "and so",
                    "therefore",
                    "thus",
                    "hence",
                    "consequently",
                ],
                "hypotactic": [
                    "because",
                    "as",
                    "since",
                    "given that",
                    "due to the fact that",
                ],
            },
            "Result": {
                "paratactic": ["in consequence", "as a result"],
                "hypotactic": ["so that", "such that"],
            },
            "Purpose": {
                "paratactic": ["for this purpose", "with this in view"],
                "hypotactic": [
                    "so that",
                    "in order that",
                    "that",
                    "lest",
                    "for fear that",
                ],
            },
            "Conditional": {
                "paratactic": ["in that case", "then", "under the circumstances"],
                "hypotactic": [
                    "if",
                    "unless",
                    "provided that",
                    "assuming that",
                    "in case",
                    "only if",
                ],
            },
            "Concessive": {
                "paratactic": [
                    "but",
                    "yet",
                    "still",
                    "nevertheless",
                    "however",
                    "even so",
                    "despite this",
                    "all the same",
                ],
                "hypotactic": [
                    "although",
                    "even though",
                    "while",
                    "though",
                    "despite the fact that",
                ],
            },
        },
        "Manner": {
            "Means": {
                "paratactic": ["thus", "thereby", "by this means"],
                "hypotactic": ["by", "through", "by means of", "via", "using"],
            },
            "Comparison": {
                "paratactic": [
                    "and similarly",
                    "so",
                    "thus",
                    "likewise",
                    "in the same way",
                ],
                "hypotactic": [
                    "as if",
                    "like",
                    "the way",
                    "as though",
                    "in a way that",
                ],
            },
            "Comparison_Negative": {
                "paratactic": ["in a different way", "otherwise"],
                "hypotactic": [],
            },
        },
        "Spatial": {
            "Same Place": {
                "paratactic": [
                    "and there",
                    "here",
                    "in that place",
                    "in the same place",
                ],
                "hypotactic": ["where", "wherever", "in which", "at which"],
            },
            "Different Place": {
                "paratactic": ["elsewhere", "in another place"],
                "hypotactic": ["away from", "beyond", "outside of"],
            },
        },
        "Matter": {
            "Positive": {
                "paratactic": ["in that respect", "as to that", "in this regard"],
                "hypotactic": [],
            },
            "Negative": {
                "paratactic": ["in other respects", "elsewhere"],
                "hypotactic": [],
            },
        },
    },
    "Extension": {
        "Addition": {
            "paratactic": [
                "and",
                "also",
                "too",
                "besides",
                "furthermore",
                "moreover",
                "in addition",
            ],
            "hypotactic": ["while", "whereas", "along with", "in addition to"],
        },
        "Variation": {
            "Replacive": {
                "paratactic": ["but not", "instead", "rather", "on the contrary"],
                "hypotactic": ["rather than", "instead of", "as opposed to"],
            },
            "Subtractive": {
                "paratactic": ["but", "except", "excluding", "save for", "apart from"],
                "hypotactic": ["except that", "but that", "other than"],
            },
            "Alternative": {
                "paratactic": ["or", "either ... or", "alternatively", "or else"],
                "hypotactic": ["if not ... then", "whether", "whether ... or not"],
            },
        },
        "Adversative": {
            "paratactic": [
                "but",
                "yet",
                "however",
                "on the other hand",
                "nevertheless",
                "still",
            ],
            "hypotactic": ["whereas", "while"],
        },
    },
    "Elaboration": {
        "Apposition": {
            "Expository": {
                "paratactic": [
                    "in other words",
                    "that is",
                    "i.e.",
                    "to say",
                    "to put it another way",
                ],
                "hypotactic": ["which", "who"],
            },
            "Exemplifying": {
                "paratactic": ["for example", "for instance", "thus", "to illustrate"],
                "hypotactic": ["as", "which is to say"],
            },
        },
        "Clarifying": {
            "Corrective": {
                "paratactic": ["or rather", "at least", "to be more precise"],
                "hypotactic": ["whereas"],
            },
            "Distractive": {
                "paratactic": ["by the way", "incidentally"],
                "hypotactic": [],
            },
            "Dismissive": {
                "paratactic": ["in any case", "anyway", "leaving that aside"],
                "hypotactic": [],
            },
            "Particularizing": {
                "paratactic": ["in particular", "more especially"],
                "hypotactic": [],
            },
            "Resumptive": {
                "paratactic": [
                    "as I was saying",
                    "to resume",
                    "to get back to the point",
                ],
                "hypotactic": [],
            },
            "Summative": {
                "paratactic": ["in short", "to sum up", "in conclusion", "briefly"],
                "hypotactic": [],
            },
            "Verificative": {
                "paratactic": ["actually", "as a matter of fact", "in fact", "indeed"],
                "hypotactic": [],
            },
        },
        "Amplification": {
            "paratactic": ["indeed", "in fact", "actually", "specifically"],
            "hypotactic": ["particularly", "notably", "especially"],
        },
    },
}