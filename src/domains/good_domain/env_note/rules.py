# 环境手工备注业务规则，预留扩展
# 当前：仅校验内容非空
def validate_note_content(content: str) -> bool:
    if not content or len(content.strip()) == 0:
        return False
    return True
