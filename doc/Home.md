# Tellify - Event Alert Dashboard System

There are many systems out there that are designed to handle event
management and alerting in a corporate environment (see Others Systems
below).  However, they tend to be oriented towards IT operations and have
architectures which are designed to be robust in the middle of
infrastructure failures.  Also, the ones that have alert systems built in
don't seem to think in terms of allowing individuals to decide what
they're interested in; you need to be a System Administrator to change
your alert subscriptions.

The goal of this system is to allow ordinary users fine-grained control of the
alerts they receive and how they receive them.

## Name Ideas
Name idears:  Party, Lanche (short for avalanche).   tellify

## Goals

Create a system which allows sending arbitrary event data into it and then
allows individual users to view and be alerted by these events.

To accomplish this, we need:

- A service which allows us to send events to it
- A way to filter/aggregate the events into intelligent data (note that
  this might be driven by user configuration).
- A way to display this data on a dashboard.
- A way to notify users when these things occur.
- A way to delete all alerts for a given user when they leave the company
  or their particular group.


## Non-Goals
- Handle epic scale (think tens of events per second, not hundreds or
  thousands).
- Be robust when underlying infrastructure is failing.

## Use-Cases
- User can get alert when disk space for any of 10 different filesystems
  exceeds 90%.  The alert should happen during work-hours, but will send
  to home email & text on evenings and weekends if they exceed 97%.
- User is normally alerted when common builds fail on their block.
- CAD owner wants to know if more than 4 blocks fail the 'place' step in
  a given sequence.

## TODO
- Create initial tests list / test plan
- The config `_id`is used to update the config object.  Any way to prevent
  user from hacking?

## Subsystems
- Event handling
- Aggregator / alerter
- Dashboard / user configuration

## Event Examples
### Periodic
- Disk /sarc/cad is now at 93.5% (every 1/2 hour)
- Host caddashboard is still alive (every minute)
- Repo bitb0:pipriv/base branch:master hasn't been modified (shouldn't
  really do this one).

### Job specific
- `project:vr0 block:gc_t route_opt user:gpupi runtag:myruntag completed status:good  tns:-50`

### Aggregated
Aggregated events are "intelligent" handlers which take other events and
merge them together.


- When more than three blocks in project:vr0 fail with the same runtag, send event.
 

## System Architecture
 


![System Architecture](Diagram1.svg)

 

### Entities

- Event Handlers (most often user code or plugins)
- Event Config (stored in mongodb or filesystem). 
- Alert parameters (mongodb or filesystem)
- Event state, one per Event Config (redis)

## Coding
- These should be written using asyncio unless there's a reason not to.
- Use black for formatting (part of git check-in?  Travis?)

### Event Handlers
Event handlers takes specific messages from the event queue and processes
them. The output can be one of:

- Nothing (except filtering hints)
- Send an alert
- Update Event State 
- Send another event

Event Handler Instances are just Config blobs associated with a specific
Event Handler.  An eid (mongodb _id in string form) is the unique key for
each.

#### Code / Methods

Each User EventHandler should inherit from tellify.EventHandler and must
define a specific set of methods for its operation.


| Method | Parameters | Notes |
| -----  | ---------  | ----- |
`title` | | Returns a one-line description of this EventHandler instance.
`description` | | Longer (paragraph) description of the handler. 
`required_fields` | | Return a list of keys that Events must have before calling this EventHandler
`get_config_parameters` | | Returns a json blob (json form Schema). 
`validate_parameters` | username, parameters | Return list of failures [ ].
`event_handler` |  event (actual Dict of the event) 

The Class Methods are:

| Function | Parameters | Notes
| -------- | ---------- | ----------------------------------------------------- 
`alert_ascii` | [ (config, alert)... ] | Given a list of config/alert entries, return with the ascii text for it (suitable for email)
`alert_html` | [ (config, alert)... ]  | Same as above, but return html format
`alert_text` | [ (config, alert)... ] | Same but return a summary suitable for a text message (one-liner).

We assume here that each of these instances are initialized with the Event
Config.  

Note that all the alert_*  methods are there to allow ganging of similar
items into a single notification.

Every EventHandler has access to the following methods:

config_parameter example

## Testing

Plan on using travis-ci from github.  It looks like you can tell it to
spin up a mongodb or redis instance as part of the test, so this should
make things easy.

##  Security
Security can be implemented by the individual Event and Alarm Handlers.

## Scaling
I've tried to make things so that they can fairly easily scale if we run
into bottlenecks. 

### Event Dispatcher

Single Instance.  This might get slow because it needs to search through
all the Event Config objects to search for what to dispatch.  It will
likely be very slow when it first comes up due to a lack of hints.

Right now, each message is read, processed and then dispatched to an Event
Handler.   There's no reason this can't be split into a round-robin pool
(multi-processed).  

### Event Handler

These are already designed to scale reasonably.  Current approach is to
Process Pool them.

If we still run out of time, then we can dask them.  They just need the
Event+Event Config and no response is checked.

### Alarm Handler

Inherits from EventHandler so has all the same configuration items.  It
has an extended API which allows sending emails and such.

Useful

https://tirkarthi.github.io/programming/2018/08/20/redis-streams-python.html

JSon schema -

https://guillotina.io/ngx-schema-form/dist/ngx-schema-form/json


## Web / API

### Entities

- User (current one logged in)
- Project membership (user is member of project xxx)   (defer)
- Event Handlers (get list, but it's mostly static)
- User Event Handler Instances (get list)
- Project Event Handler (defer)
- Event Handler Config Templates (partially filled out configuration items) (defer)
- Event Handler Config Instances (tie Config items to User Alert)
- User Alert Styles
- User Alert List (ties User Event Handler Instances
 

### Operations
- Show list of User Event Handler Instances.
- Show list of possible alerts and status (status is either fired or not).
- Allow user to Add New Event Handler Instance.  Select Event Handler
  which pops up the dialog to create a new Event Handler Instance for that
  user.
- Edit User Event Handler Instances
- Add Alert Styles (email, text message, may change at different times.
  How long to wait for aggregating).
- Tie User Event Handlers to User Alerts
- Allow user to clear alerts.
- Question: should we try and make this "live" updates (events show up
  immediately)?

 

## Misc

### Decisions to Make
* Redis pub/sub or Redis Streams?
* Config file format / location
* For demo - docker instance?
* For demo / backend - flask?
* Which license for github?  I see Samsung Electronics has MIT, LGPL, Creative Commons, BSD-3, BSD-2.  I lean towards MIT.

### Rejected
* Originally thought of using Kafka or Rabbitmq for the pub/sub.  But I really needed something to be a local cache of state and redis looked ideal.  Since it does pub/sub (as well as the new streams!), it seemed ideal just to use a single server.
* I thought about putting formal locks around each event handler's getting and setting of Event Handler Instance state, but that seemed clunky.  Currently exposing the full redis API so that each Event Handler can do what's necessary to make sure simultaneous updates don't stomp on each-other.
* Thought have having the Event Handler actually do the alerting, but that would prevent pulling multiple alerts together into a single message.
* One major question was whether to use Redis Pub/Sub (rabbitmq style messages) or Redis Streams (Kafkaesque) style.  Decided on Pub/Sub - it's less recoverable from disasters, but easier to implement.

### Random Idears
* User can select how long to aggregate events before emailing them.  The default is to wait a minute, but we could do something like "alert me every minute, but after 7PM, aggregate everything till 6AM".
* Should we keep a count of items fired in the alert stream?
* Should the `alert_` methods be passed the complete list of alerts available at that time (even ones from other EventHandlers)?  That would allow better aggregation across AlertTypes.  It would mean that the return information would have to include handled Events.
