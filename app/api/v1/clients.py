"""Client management API endpoints (Mandantenverwaltung)."""

import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.models.client import Client
from app.schemas.client import (
    ClientCreate,
    ClientList,
    ClientListItem,
    ClientResponse,
    ClientStats,
    ClientUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _check_client_access(user) -> None:
    """Check if user can manage clients."""
    if not user.can_manage_clients():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Mandantenverwaltung erfordert den Steuerberater-Plan.",
        )


@router.get(
    "/",
    response_model=ClientList,
    summary="List clients",
    description="Get all clients for the current user.",
)
async def list_clients(
    current_user: CurrentUser,
    db: DbSession,
    page: int = 1,
    page_size: int = 20,
    active_only: bool = False,
    search: str | None = None,
) -> ClientList:
    """List all clients for the current user."""
    _check_client_access(current_user)

    # Build query
    query = select(Client).where(Client.user_id == current_user.id)

    if active_only:
        query = query.where(Client.is_active == True)

    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Client.name.ilike(search_term)) |
            (Client.client_number.ilike(search_term)) |
            (Client.contact_name.ilike(search_term))
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    query = query.order_by(Client.name).offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    clients = result.scalars().all()

    return ClientList(
        items=[
            ClientListItem(
                id=client.id,
                name=client.name,
                client_number=client.client_number,
                is_active=client.is_active,
                validation_count=client.validation_count,
                last_validation_at=client.last_validation_at,
                created_at=client.created_at,
            )
            for client in clients
        ],
        total=total,
        page=page,
        page_size=page_size,
        max_clients=current_user.get_max_clients(),
    )


@router.get(
    "/stats",
    response_model=ClientStats,
    summary="Get client statistics",
    description="Get statistics about clients.",
)
async def get_client_stats(
    current_user: CurrentUser,
    db: DbSession,
) -> ClientStats:
    """Get client statistics for the current user."""
    _check_client_access(current_user)

    # Total clients
    total_result = await db.execute(
        select(func.count(Client.id)).where(Client.user_id == current_user.id)
    )
    total_clients = total_result.scalar() or 0

    # Active clients
    active_result = await db.execute(
        select(func.count(Client.id)).where(
            Client.user_id == current_user.id,
            Client.is_active == True,
        )
    )
    active_clients = active_result.scalar() or 0

    # Total validations across all clients
    validations_result = await db.execute(
        select(func.sum(Client.validation_count)).where(Client.user_id == current_user.id)
    )
    total_validations = validations_result.scalar() or 0

    return ClientStats(
        total_clients=total_clients,
        active_clients=active_clients,
        total_validations=total_validations,
        max_clients=current_user.get_max_clients(),
    )


@router.post(
    "/",
    response_model=ClientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create client",
    description="Create a new client.",
)
async def create_client(
    data: ClientCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> ClientResponse:
    """Create a new client."""
    _check_client_access(current_user)

    # Check if user has reached max clients
    count_result = await db.execute(
        select(func.count(Client.id)).where(Client.user_id == current_user.id)
    )
    current_count = count_result.scalar() or 0
    max_clients = current_user.get_max_clients()

    if current_count >= max_clients:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximale Anzahl von {max_clients} Mandanten erreicht.",
        )

    # Create client
    client = Client(
        user_id=current_user.id,
        name=data.name,
        client_number=data.client_number,
        tax_number=data.tax_number,
        vat_id=data.vat_id,
        contact_name=data.contact_name,
        contact_email=data.contact_email,
        contact_phone=data.contact_phone,
        street=data.street,
        postal_code=data.postal_code,
        city=data.city,
        country=data.country,
        notes=data.notes,
    )

    db.add(client)
    await db.commit()
    await db.refresh(client)

    logger.info(f"Client created: user={current_user.email}, client={client.name}")

    return _client_to_response(client)


@router.get(
    "/{client_id}",
    response_model=ClientResponse,
    summary="Get client",
    description="Get details for a specific client.",
)
async def get_client(
    client_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> ClientResponse:
    """Get details for a specific client."""
    _check_client_access(current_user)

    client = await _get_client_or_404(client_id, current_user.id, db)
    return _client_to_response(client)


@router.patch(
    "/{client_id}",
    response_model=ClientResponse,
    summary="Update client",
    description="Update a client's information.",
)
async def update_client(
    client_id: UUID,
    data: ClientUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> ClientResponse:
    """Update a client."""
    _check_client_access(current_user)

    client = await _get_client_or_404(client_id, current_user.id, db)

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(client, field, value)

    await db.commit()
    await db.refresh(client)

    logger.info(f"Client updated: user={current_user.email}, client={client.name}")

    return _client_to_response(client)


@router.delete(
    "/{client_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete client",
    description="Delete a client and all associated data.",
)
async def delete_client(
    client_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    """Delete a client."""
    _check_client_access(current_user)

    client = await _get_client_or_404(client_id, current_user.id, db)

    await db.delete(client)
    await db.commit()

    logger.info(f"Client deleted: user={current_user.email}, client_id={client_id}")


async def _get_client_or_404(client_id: UUID, user_id: UUID, db: DbSession) -> Client:
    """Get a client by ID or raise 404."""
    result = await db.execute(
        select(Client).where(
            Client.id == client_id,
            Client.user_id == user_id,
        )
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mandant nicht gefunden.",
        )

    return client


def _client_to_response(client: Client) -> ClientResponse:
    """Convert Client model to response schema."""
    return ClientResponse(
        id=client.id,
        name=client.name,
        client_number=client.client_number,
        tax_number=client.tax_number,
        vat_id=client.vat_id,
        contact_name=client.contact_name,
        contact_email=client.contact_email,
        contact_phone=client.contact_phone,
        street=client.street,
        postal_code=client.postal_code,
        city=client.city,
        country=client.country,
        notes=client.notes,
        is_active=client.is_active,
        validation_count=client.validation_count,
        last_validation_at=client.last_validation_at,
        created_at=client.created_at,
        updated_at=client.updated_at,
    )
