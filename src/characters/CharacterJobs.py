#Provides definitions and functional checks for different character job types
#(e.g. key geneartion or research).

#####  Imports  #####

from enum import IntEnum, verify, UNIQUE

#####  Package Variables  #####

#####  Enum Classes  #####

@verify(UNIQUE)
class CharacterJobTypeEnum(IntEnum):

    UNOCCUPIED        =    0
    #Order of this section is to match the ECON table.
    BUILDER_t0        =    1
    BUILDER_t1        =    2
    BUILDER_t2        =    3
    BUILDER_t3        =    4
    BUILDER_t4        =    5
    BUILDER_t5        =    6
    CRAFTER_t0        =    7
    CRAFTER_t1        =    8
    CRAFTER_t2        =    9
    CRAFTER_t3        =   10
    CRAFTER_t4        =   11
    CRAFTER_t5        =   12
    HOSPITAL_t0       =   13
    HOSPITAL_t1       =   14
    HOSPITAL_t2       =   15
    HOSPITAL_t3       =   16
    HOSPITAL_t4       =   17
    HOSPITAL_t5       =   18
    KEY_GENERATION_t0 =   19
    KEY_GENERATION_t1 =   20
    KEY_GENERATION_t2 =   21
    KEY_GENERATION_t3 =   22
    KEY_GENERATION_t4 =   23
    KEY_GENERATION_t5 =   24
    RESEARCH_t0       =   25
    RESEARCH_t1       =   26
    RESEARCH_t2       =   27
    RESEARCH_t3       =   28
    RESEARCH_t4       =   29
    RESEARCH_t5       =   30
    DUNGEON_TEAM_t0   =   31
    DUNGEON_TEAM_t1   =   32
    DUNGEON_TEAM_t2   =   33
    DUNGEON_TEAM_t3   =   34
    DUNGEON_TEAM_t4   =   35
    DUNGEON_TEAM_t5   =   36
    WORKER_t0         =   37
    WORKER_t1         =   38
    WORKER_t2         =   39
    WORKER_t3         =   40
    WORKER_t4         =   41
    WORKER_t5         =   42
