
@app.patch("/items/{item_id}")
def update_item(item_id: int, updates: dict, session: Session = Depends(get_session)):
    item = session.get(NewsItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
        
    # Apply updates
    for key, value in updates.items():
        if hasattr(item, key):
            setattr(item, key, value)
    
    session.add(item)
    session.commit()
    session.refresh(item)
    return item
