from backend.services.gmail import sync_gmail_messages

if __name__ == "__main__":
    result = sync_gmail_messages()
    print(
        "Gmail sync complete: "
        f"{result.imported_count} imported, "
        f"{result.updated_count} updated, "
        f"{result.scanned_count} scanned for {result.email_address}."
    )
