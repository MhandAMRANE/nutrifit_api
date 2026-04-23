from sqlalchemy.orm import Session
from sqlalchemy import or_
from models import Utilisateur, Friendship, SharedRecipe, Recette
from fastapi import HTTPException

def get_friends(db: Session, user_id: int):
    friendships = db.query(Friendship).filter(
        or_(Friendship.requester_id == user_id, Friendship.receiver_id == user_id),
        Friendship.status == 'accepted'
    ).all()
    
    friend_ids = []
    for f in friendships:
        if f.requester_id == user_id:
            friend_ids.append(f.receiver_id)
        else:
            friend_ids.append(f.requester_id)
            
    return db.query(Utilisateur).filter(Utilisateur.id_utilisateur.in_(friend_ids)).all()

def get_friend_requests(db: Session, user_id: int):
    requests = db.query(Friendship).filter(
        Friendship.receiver_id == user_id,
        Friendship.status == 'pending'
    ).all()
    
    for req in requests:
        user = db.query(Utilisateur).filter(Utilisateur.id_utilisateur == req.requester_id).first()
        setattr(req, "ami", user)
    return requests

def send_friend_request(db: Session, requester_id: int, receiver_id: int):
    if requester_id == receiver_id:
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas vous ajouter vous-même en ami.")
    
    target = db.query(Utilisateur).filter(Utilisateur.id_utilisateur == receiver_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé.")
        
    existing = db.query(Friendship).filter(
        or_(
            (Friendship.requester_id == requester_id) & (Friendship.receiver_id == receiver_id),
            (Friendship.requester_id == receiver_id) & (Friendship.receiver_id == requester_id)
        )
    ).first()
    
    if existing:
        if existing.status == 'pending':
            raise HTTPException(status_code=400, detail="Une demande est déjà en attente.")
        elif existing.status == 'accepted':
            raise HTTPException(status_code=400, detail="Vous êtes déjà amis.")
        elif existing.status == 'rejected':
            existing.status = 'pending'
            existing.requester_id = requester_id
            existing.receiver_id = receiver_id
            db.commit()
            db.refresh(existing)
            return existing
            
    new_req = Friendship(requester_id=requester_id, receiver_id=receiver_id, status='pending')
    db.add(new_req)
    db.commit()
    db.refresh(new_req)
    return new_req

def accept_friend_request(db: Session, request_id: int, user_id: int):
    req = db.query(Friendship).filter(Friendship.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Demande introuvable.")
    if req.receiver_id != user_id:
        raise HTTPException(status_code=403, detail="Non autorisé.")
    if req.status != 'pending':
        raise HTTPException(status_code=400, detail="La demande n'est pas en attente.")
        
    req.status = 'accepted'
    db.commit()
    db.refresh(req)
    return req

def reject_friend_request(db: Session, request_id: int, user_id: int):
    req = db.query(Friendship).filter(Friendship.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Demande introuvable.")
    if req.receiver_id != user_id and req.requester_id != user_id:
        raise HTTPException(status_code=403, detail="Non autorisé.")
        
    db.delete(req)
    db.commit()
    return True

def remove_friend(db: Session, user_id: int, friend_id: int):
    friendship = db.query(Friendship).filter(
        or_(
            (Friendship.requester_id == user_id) & (Friendship.receiver_id == friend_id),
            (Friendship.requester_id == friend_id) & (Friendship.receiver_id == user_id)
        ),
        Friendship.status == 'accepted'
    ).first()
    
    if not friendship:
        raise HTTPException(status_code=404, detail="Amitié introuvable.")
        
    db.delete(friendship)
    db.commit()
    return True

def search_users(db: Session, query: str, current_user_id: int):
    friends = get_friends(db, current_user_id)
    friend_ids = [f.id_utilisateur for f in friends]
    
    users = db.query(Utilisateur).filter(
        Utilisateur.nom.ilike(f"%{query}%"),
        Utilisateur.id_utilisateur != current_user_id
    ).limit(20).all()
    
    results = []
    for u in users:
        results.append({
            "id_utilisateur": u.id_utilisateur,
            "nom": u.nom,
            "prenom": u.prenom,
            "path_pp": u.path_pp,
            "is_friend": u.id_utilisateur in friend_ids
        })
    return results

def get_stats(db: Session, profile_user_id: int, current_user_id: int) -> dict:
    friends_count = db.query(Friendship).filter(
        or_(Friendship.requester_id == profile_user_id, Friendship.receiver_id == profile_user_id),
        Friendship.status == 'accepted'
    ).count()

    return {
        "id_utilisateur": profile_user_id,
        "friends_count": friends_count,
    }

def share_recipe(db: Session, sender_id: int, receiver_ids: list[int], recipe_id: int):
    for r_id in receiver_ids:
        friendship = db.query(Friendship).filter(
            or_(
                (Friendship.requester_id == sender_id) & (Friendship.receiver_id == r_id),
                (Friendship.requester_id == r_id) & (Friendship.receiver_id == sender_id)
            ),
            Friendship.status == 'accepted'
        ).first()
        if not friendship:
            raise HTTPException(status_code=403, detail=f"L'utilisateur {r_id} n'est pas votre ami.")
            
    shared_entries = []
    for r_id in receiver_ids:
        new_share = SharedRecipe(sender_id=sender_id, receiver_id=r_id, recipe_id=recipe_id)
        db.add(new_share)
        shared_entries.append(new_share)
        
    db.commit()
    for entry in shared_entries:
        db.refresh(entry)
    return shared_entries

def get_shared_recipes_with_me(db: Session, user_id: int):
    shared = db.query(SharedRecipe).filter(SharedRecipe.receiver_id == user_id).order_by(SharedRecipe.created_at.desc()).all()
    
    results = []
    for share in shared:
        recette = db.query(Recette).filter(Recette.id_recette == share.recipe_id).first()
        sender = db.query(Utilisateur).filter(Utilisateur.id_utilisateur == share.sender_id).first()
        
        setattr(share, "recette", recette)
        setattr(share, "sender", sender)
        
        results.append(share)
        
    return results
