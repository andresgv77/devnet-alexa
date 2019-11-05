"""
devnet_skill.py
Purpose:
    lambda hander for the DevNet Alexa Data Center Skill
Author:
    John McDonough (jomcdono@cisco.com)
     Cisco Systems, Inc.
CoAuthor:    
    Andrés Guevara y Matheo López
    UDLA   
"""
from __future__ import print_function


# Importar las funciones de gestión de UCS
import ucsm_operations

# --------------- Ayudantes que construyen todas las respuestas ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Funciones que controlan el comportamiento de la habilidad ------------------

def get_welcome_response():

    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Bienvenido a la Habilidad DevNet Alexa para la Gestión del UCS" \
                    "Se puede decir cosas como: ¿Cuál es el recuento de mi cuenta de fallas?" \
                    "O se puede decir Añadir V Lan 100" \
                    "O puedes decir Aprovisionar un servidor"
    # Si el usuario no responde al mensaje de bienvenida o dice algo
    # que no se entiende, se les volverá a preguntar con este texto.
    reprompt_text = "¿Desea hacer algo o saber algo sobre su sistema UCS?"
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def handle_session_end_request():
    card_title = "Sesión finalizada"
    speech_output = "Gracias por usar Alexa Skill para la administración de UCS"

    # Establecer esto en verdadero finaliza la sesión y sale de la habilidad.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))

# Obtenga las fallas UCS
def get_faults(intent, session):
    session_attributes = {}
    reprompt_text = None

    speech_output = ucsm_operations.get_ucs_faults()
    should_end_session = True

    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))

# Agregar una VLAN UCS
def add_vlan(intent, session):
    session_attributes = {}
    reprompt_text = None

    speech_output = ucsm_operations.add_ucs_vlan(intent['slots']['vlan_id']['value'])
    should_end_session = True

    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))

# Eliminar una VLAN UCS
def remove_vlan(intent, session):
    session_attributes = {}
    reprompt_text = None

    speech_output = ucsm_operations.remove_ucs_vlan(intent['slots']['vlan_id']['value'])
    should_end_session = True

    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))

# Crear y asociar un perfil de servicio a un servidor disponible
def set_server(intent, session):
    session_attributes = {}
    reprompt_text = None

    speech_output = result = ucsm_operations.set_ucs_server()
    should_end_session = True

    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))

# --------------- Eventos ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Despacho para el lanzamiento de tu habilidad
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Despacho a los manejadores de intención de tu habilidad
    if intent_name == "GetFaults":         # Punto de entrada para la intención GetFaults que creó
        return get_faults(intent, session)
    elif intent_name == "AddVlan":         # Punto de entrada para la intención AddVlan que creó
        return add_vlan(intent, session)
    elif intent_name == "RemoveVlan":      # Punto de entrada para la intención RemoveVlan que puede haber creado :)
        return remove_vlan(intent, session)
    elif intent_name == "ProvisionServer": # Punto de entrada para la intención de ProvisionServer que creó
        return set_server(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # agregar lógica de limpieza aquí


# --------------- Controlador principal ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
