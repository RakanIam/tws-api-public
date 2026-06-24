import plistlib

OBJ = "￼"


def token_string(template):
    result = ""
    attachments = {}
    i = 0
    while i < len(template):
        if template[i] == "{":
            end = template.index("}", i)
            var_name = template[i + 1 : end]
            pos = len(result)
            result += OBJ
            attachments[f"{{{pos}, 1}}"] = {
                "Type": "Variable",
                "VariableName": var_name,
            }
            i = end + 1
        else:
            result += template[i]
            i += 1

    if not attachments:
        return template

    return {
        "Value": {
            "attachmentsByRange": attachments,
            "string": result,
        },
        "WFSerializationType": "WFTextTokenString",
    }


def named_var(name):
    return token_string(f"{{{name}}}")


actions = []

# --- 1. Ask for phone number ---
actions.append(
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.ask",
        "WFWorkflowActionParameters": {
            "WFAskActionPrompt": "Recipient phone number\n(with country code, e.g. 966501234567)",
            "WFInputType": "Text",
            "WFAskActionDefaultAnswer": "",
        },
    }
)

# --- 2. Set Variable "Phone" ---
actions.append(
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "Phone",
        },
    }
)

# --- 3. Ask for message ---
actions.append(
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.ask",
        "WFWorkflowActionParameters": {
            "WFAskActionPrompt": "Message to send",
            "WFInputType": "Text",
            "WFAskActionDefaultAnswer": "",
        },
    }
)

# --- 4. Set Variable "Msg" ---
actions.append(
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "Msg",
        },
    }
)

# --- 5. Ask for date/time ---
actions.append(
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.ask",
        "WFWorkflowActionParameters": {
            "WFAskActionPrompt": "When should the message be sent?",
            "WFInputType": "Date and Time",
        },
    }
)

# --- 6. Set Variable "SendTime" ---
actions.append(
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "SendTime",
        },
    }
)

# --- 7. URL Encode the message ---
actions.append(
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.urlencode",
        "WFWorkflowActionParameters": {
            "WFInput": named_var("Msg"),
        },
    }
)

# --- 8. Set Variable "EncodedMsg" ---
actions.append(
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "EncodedMsg",
        },
    }
)

# --- 9. Build WhatsApp URL ---
actions.append(
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.gettext",
        "WFWorkflowActionParameters": {
            "WFTextActionText": token_string(
                "https://wa.me/{Phone}?text={EncodedMsg}"
            ),
        },
    }
)

# --- 10. Set Variable "WALink" ---
actions.append(
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "WALink",
        },
    }
)

# --- 11. Build reminder notes ---
actions.append(
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.gettext",
        "WFWorkflowActionParameters": {
            "WFTextActionText": token_string(
                "Tap the link below to open WhatsApp and send your message:\n\n{WALink}\n\nMessage: {Msg}\nTo: {Phone}"
            ),
        },
    }
)

# --- 12. Set Variable "Notes" ---
actions.append(
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "Notes",
        },
    }
)

# --- 13. Build reminder title ---
actions.append(
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.gettext",
        "WFWorkflowActionParameters": {
            "WFTextActionText": token_string(
                "WhatsApp to {Phone}: {Msg}"
            ),
        },
    }
)

# --- 14. Set Variable "Title" ---
actions.append(
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "Title",
        },
    }
)

# --- 15. Add New Reminder ---
actions.append(
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.addnewreminder",
        "WFWorkflowActionParameters": {
            "WFCalendarItemTitle": named_var("Title"),
            "WFCalendarItemNotes": named_var("Notes"),
            "WFCalendarItemDueDate": named_var("SendTime"),
            "WFRemindMeWhen": 0,
        },
    }
)

# --- 16. Format the send time for display ---
actions.append(
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.format.date",
        "WFWorkflowActionParameters": {
            "WFDateFormatStyle": "Medium",
            "WFTimeFormatStyle": "Short",
            "WFDate": named_var("SendTime"),
        },
    }
)

# --- 17. Set Variable "DisplayTime" ---
actions.append(
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.setvariable",
        "WFWorkflowActionParameters": {
            "WFVariableName": "DisplayTime",
        },
    }
)

# --- 18. Show confirmation ---
actions.append(
    {
        "WFWorkflowActionIdentifier": "is.workflow.actions.alert",
        "WFWorkflowActionParameters": {
            "WFAlertActionTitle": "Message Scheduled!",
            "WFAlertActionMessage": token_string(
                "A reminder is set for {DisplayTime}.\n\nWhen it fires, tap the wa.me link to open WhatsApp Business with your message pre-filled, then hit Send.\n\nTo: {Phone}\nMessage: {Msg}"
            ),
            "WFAlertActionCancelButtonShown": False,
        },
    }
)

shortcut = {
    "WFWorkflowMinimumClientVersionString": "900",
    "WFWorkflowMinimumClientVersion": 900,
    "WFWorkflowIcon": {
        "WFWorkflowIconStartColor": 4292093695,
        "WFWorkflowIconGlyphNumber": 59511,
    },
    "WFWorkflowClientVersion": "2302.0.4",
    "WFWorkflowOutputContentItemClasses": [],
    "WFWorkflowHasOutputFallback": False,
    "WFWorkflowActions": actions,
    "WFWorkflowImportQuestions": [],
    "WFWorkflowInputContentItemClasses": [],
    "WFWorkflowTypes": [],
    "WFQuickActionSurfaces": [],
    "WFWorkflowHasShortcutInputVariables": False,
}

output_path = "Schedule_WhatsApp_Message.shortcut"
with open(output_path, "wb") as f:
    plistlib.dump(shortcut, f, fmt=plistlib.FMT_BINARY)

print(f"Created: {output_path}")
