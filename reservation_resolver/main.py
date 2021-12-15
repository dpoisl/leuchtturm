#!/usr/bin/env python

import collections
import csv
import datetime
import logging
import random
from typing import Counter, Iterable, List, NamedTuple

Reservation = NamedTuple(
    "Reservation", [("start", datetime.date), ("end", datetime.date), ("name", str)]
)


ROOMS = 2
_LOGGER = logging.getLogger("")


def date_range(
    start: datetime.date, end: datetime.date, step=datetime.timedelta(days=1)
) -> Counter[datetime.date]:
    """Yield a range of dates INCLUSIVE on both ends."""
    current = start
    while current < end:
        yield current
        current += step


def create_availability(reservations: List[Reservation]) -> Counter[datetime.date]:
    """
    Initialize availability counter with # of free rooms per day.

    :param reservations: list of reservations, start and end date are taken from those
    :return: counter with each day between start and end set to the number of available rooms
    """
    min_date = min(x.start for x in reservations)
    max_date = max(x.end for x in reservations)
    _LOGGER.info(
        "Creating day counters for %d rooms between %s and %s",
        ROOMS,
        min_date,
        max_date,
    )
    availability = collections.Counter()
    for date in date_range(min_date, max_date):
        availability[date] = ROOMS
    return availability


def pick_reservation(reservations: List[Reservation]) -> Reservation:
    """
    Randomly pick a reservation from the list of reservations.

    This reservation will be granted and all conflicting reservations will get removed.
    Uses SystemRandom to get a nice true random number on all platforms.

    :param reservations: list of reservations to pick from
    :return: the picked reservation
    """
    _LOGGER.debug("Reservattion pool for picking is %r", reservations)
    picked = random.SystemRandom().choice(reservations)
    reservations.remove(picked)
    _LOGGER.info("Picked reservation %r", picked)
    return picked


def remove_conflicting(
    reservations: List[Reservation], availability: Counter[datetime.date]
) -> None:
    """
    Remove all reservations where at least one day is not available anymore.

    :param reservations: reservations to prunt
    :param availability: room availability list
    """
    _LOGGER.debug(
        "Removing unavailable reservations from %r based on counters %r",
        reservations,
        availability,
    )
    all_reservations = reservations[:]
    for reservation in all_reservations:
        if any(
            availability[date] == 0
            for date in date_range(reservation.start, reservation.end)
        ):
            reservations.remove(reservation)
            _LOGGER.info("Removing reservation %r", reservation)
    _LOGGER.debug("After removing left with reservations %r", reservations)


def update_availability(reservation: Reservation, availability: Counter[datetime.date]) -> None:
    """
    Update room availability when a given reservation is picked.

    Deduces 1 from all days in a given reservation.

    :param reservation: picked reservation
    :param availability: room availability to update
    """
    _LOGGER.debug(
        "Updating availability for reservation %r, current counters are %r",
        reservation,
        availability,
    )
    for day in date_range(reservation.start, reservation.end):
        availability[day] -= 1
        if availability[day] < 0:
            raise ValueError(f"Reservation {reservation} goes <0 at date {day}")
    _LOGGER.debug(
        "After updating availability for reservation %r counters are %r",
        reservation,
        availability,
    )


def read_reservations(filename: str) -> List[Reservation]:
    """
    Read requested reservations from csv file.

    No error handling. Write sensible files.

    :param filename: file to read
    :return: list of parsed reservation objects
    """
    result = []
    with open(filename) as csv_file:
        reader = csv.reader(csv_file, delimiter=";", quotechar='"')
        for row in reader:
            result.append(
                Reservation(
                    start=datetime.datetime.strptime(row[0], "%Y-%m-%d").date(),
                    end=datetime.datetime.strptime(row[1], "%Y-%m-%d").date(),
                    name=row[2],
                )
            )
    return result


def print_chosen(chosen: Iterable[Reservation]) -> None:
    """
    Print the list of picked reservations.

    :param chosen: picked reservations
    """
    print("Picked reservations:")
    for reservation in chosen:
        print(f"    {reservation.name} ({reservation.start} .. {reservation.end})")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    requests = read_reservations("requests.csv")
    availablility = create_availability(requests)
    chosen = []
    while len(requests):
        picked = pick_reservation(requests)
        update_availability(picked, availablility)
        remove_conflicting(requests, availablility)
        chosen.append(picked)
    print_chosen(chosen)
