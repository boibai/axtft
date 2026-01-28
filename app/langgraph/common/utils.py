def stringify_history(history):

    lines = []

    for h in history:
        if h["role"] not in ("user", "assistant"):
            continue

        lines.append(f'{h["role"]}: {h["content"]}')
        
    return "\n".join(lines)

