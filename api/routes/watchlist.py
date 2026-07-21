from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.schemas import WatchlistRequest, WatchlistResponse, UserPreferences
from api.deps import get_db, get_current_user
from db.models import User, Program, UserWatchlist

router = APIRouter()

@router.get("/watchlist", response_model=List[WatchlistResponse])
def get_watchlist(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    watchlist = db.query(UserWatchlist).filter(UserWatchlist.user_id == user.id).all()
    res = []
    for w in watchlist:
        res.append({
            "program_id": w.program_id,
            "program_name": w.program.name if w.program else None,
            "muted": w.muted
        })
    return res

@router.post("/watchlist", response_model=WatchlistResponse)
def add_to_watchlist(req: WatchlistRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    program = db.query(Program).filter(Program.id == req.program_id).first()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
        
    w = db.query(UserWatchlist).filter(UserWatchlist.user_id == user.id, UserWatchlist.program_id == req.program_id).first()
    if w:
        w.muted = req.muted
    else:
        w = UserWatchlist(user_id=user.id, program_id=req.program_id, muted=req.muted)
        db.add(w)
    
    db.commit()
    return {"program_id": w.program_id, "program_name": program.name, "muted": w.muted}

@router.delete("/watchlist/{program_id}")
def remove_from_watchlist(program_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    w = db.query(UserWatchlist).filter(UserWatchlist.user_id == user.id, UserWatchlist.program_id == program_id).first()
    if not w:
        raise HTTPException(status_code=404, detail="Not in watchlist")
    db.delete(w)
    db.commit()
    return {"status": "removed"}

@router.get("/users/me/preferences", response_model=UserPreferences)
def get_preferences(user: User = Depends(get_current_user)):
    return {"notify_instant": user.notify_instant, "digest_freq": user.digest_freq}

@router.put("/users/me/preferences", response_model=UserPreferences)
def update_preferences(req: UserPreferences, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user.notify_instant = req.notify_instant
    user.digest_freq = req.digest_freq
    db.commit()
    return {"notify_instant": user.notify_instant, "digest_freq": user.digest_freq}
