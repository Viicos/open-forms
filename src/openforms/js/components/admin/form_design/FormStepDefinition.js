/*
global URLify;
 */
import get from 'lodash/get';
import React from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import {Checkbox, TextInput} from 'components/admin/forms/Inputs';
import Field, {normalizeErrors} from 'components/admin/forms/Field';
import MessageList from 'components/admin/MessageList';
import FormRow from 'components/admin/forms/FormRow';
import FormIOBuilder from 'components/formio_builder/builder';

import useDetectConfigurationChanged from './useDetectConfigurationChanged';
import ChangedFormDefinitionWarning from './ChangedFormDefinitionWarning';
import PluginWarning from './PluginWarning';
import AuthenticationWarning from './AuthenticationWarning';
import useDetectSimpleLogicErrors from './useDetectSimpleLogicErrors';
import LogicWarning from './LogicWarning';

const emptyConfiguration = {
  display: 'form',
};

/**
 * Load the form builder for a given form definition.
 *
 * Note that the underlying FormIOBuilder creates a ref from the configuration. The
 * actual builder state is maintained by FormioJS itself and we are not driven that
 * state via props - only the initial state!
 *
 * We can solely use the onChange handler to keep track of our own 'application'
 * state to eventually persist the data. This goes against React's best practices,
 * but we're fighting the library at this point.
 *
 */
const FormStepDefinition = ({
  url = '',
  generatedId = '',
  name = '',
  internalName = '',
  slug = '',
  previousText = '',
  saveText = '',
  nextText = '',
  loginRequired = false,
  isReusable = false,
  configuration = emptyConfiguration,
  onChange,
  onComponentMutated,
  onFieldChange,
  onLiteralFieldChange,
  errors,
  ...props
}) => {
  const setSlug = () => {
    // do nothing if there's already a slug set
    if (slug) return;

    // sort-of taken from Django's jquery prepopulate module
    const newSlug = URLify(name, 100, false);
    onFieldChange({
      target: {
        name: 'slug',
        value: newSlug,
      },
    });
  };

  const {changed, affectedForms} = useDetectConfigurationChanged(url, configuration);
  const {warnings} = useDetectSimpleLogicErrors(configuration);
  const componentErrors = getComponentValidationErrors(configuration, errors).map(
    ({component, field, componentLocation, message}) => {
      const location = componentLocation.trim() ? (
        <FormattedMessage
          description="Formio configuration backend validation error location suffix"
          defaultMessage={`, at location "{location}"`}
          values={{location: componentLocation}}
        />
      ) : (
        ''
      );
      return {
        level: 'error',
        message: (
          <FormattedMessage
            description="Formio configuration backend validation error for specific component property"
            defaultMessage={`The component "{label}" (with key "{key}"{location}) has a problem in the field "{field}": {error}`}
            values={{
              field,
              label: component.label,
              key: component.key,
              location,
              error: message,
            }}
          />
        ),
      };
    }
  );

  return (
    <>
      <ChangedFormDefinitionWarning changed={changed} affectedForms={affectedForms} />
      <PluginWarning loginRequired={loginRequired} configuration={configuration} />
      <AuthenticationWarning loginRequired={loginRequired} configuration={configuration} />
      <LogicWarning warnings={warnings} />

      <fieldset className="module aligned">
        <h2>
          <FormattedMessage
            description="Form definition module title"
            defaultMessage="Form definition"
          />
        </h2>

        <FormRow>
          <Field
            name="name"
            label={
              <FormattedMessage defaultMessage="Step name" description="Form step name label" />
            }
            helpText={
              <FormattedMessage
                defaultMessage="Name of the form definition used in this form step"
                description="Form step name field help text"
              />
            }
            required
            fieldBox
          >
            <TextInput value={name} onChange={onFieldChange} onBlur={setSlug} />
          </Field>
          <Field
            name="internalName"
            label={
              <FormattedMessage
                defaultMessage="Internal step name"
                description="Form step internal name label"
              />
            }
            helpText={
              <FormattedMessage
                defaultMessage="Internal name of the form definition used in this form step"
                description="Form step internal name field help text"
              />
            }
            fieldBox
          >
            <TextInput value={internalName} onChange={onFieldChange} />
          </Field>
          <Field
            name="slug"
            label={
              <FormattedMessage defaultMessage="Step slug" description="Form step slug label" />
            }
            helpText={
              <FormattedMessage
                defaultMessage="Slug of the form definition used in this form step"
                description="Form step slug field help text"
              />
            }
            required
            fieldBox
          >
            <TextInput value={slug} onChange={onFieldChange} />
          </Field>
        </FormRow>
        <FormRow>
          <Field
            name="previousText"
            label={
              <FormattedMessage
                defaultMessage="Previous text"
                description="Form step previous text label"
              />
            }
            helpText={
              <FormattedMessage
                defaultMessage="The text that will be displayed in the form step to go to the previous step. Leave blank to get value from global configuration."
                description="Form step previous text field help text"
              />
            }
            fieldBox
          >
            <TextInput value={previousText} onChange={onLiteralFieldChange} maxLength="50" />
          </Field>
          <Field
            name="saveText"
            label={
              <FormattedMessage
                defaultMessage="Save text"
                description="Form step save text label"
              />
            }
            helpText={
              <FormattedMessage
                defaultMessage="The text that will be displayed in the form step to save the current information. Leave blank to get value from global configuration."
                description="Form step save text field help text"
              />
            }
            fieldBox
          >
            <TextInput value={saveText} onChange={onLiteralFieldChange} maxLength="50" />
          </Field>
          <Field
            name="nextText"
            label={
              <FormattedMessage
                defaultMessage="Next text"
                description="Form step next text label"
              />
            }
            helpText={
              <FormattedMessage
                defaultMessage="The text that will be displayed in the form step to go to the next step. Leave blank to get value from global configuration."
                description="Form step next text field help text"
              />
            }
            fieldBox
          >
            <TextInput value={nextText} onChange={onLiteralFieldChange} maxLength="50" />
          </Field>
        </FormRow>
        <FormRow>
          <Field
            name="loginRequired"
            errorClassPrefix={'checkbox'}
            errorClassModifier={'no-padding'}
          >
            <Checkbox
              label={
                <FormattedMessage
                  defaultMessage="Login required?"
                  description="Form step login required label"
                />
              }
              name="loginRequired"
              checked={loginRequired}
              onChange={e =>
                onFieldChange({target: {name: 'loginRequired', value: !loginRequired}})
              }
            />
          </Field>
        </FormRow>
        <FormRow>
          <Field name="isReusable" errorClassPrefix={'checkbox'} errorClassModifier={'no-padding'}>
            <Checkbox
              label={
                <FormattedMessage
                  defaultMessage="Is reusable?"
                  description="Form step is reusable label"
                />
              }
              name="isReusable"
              checked={isReusable}
              onChange={e => onFieldChange({target: {name: 'isReusable', value: !isReusable}})}
            />
          </Field>
        </FormRow>
      </fieldset>

      <h2>Velden</h2>

      <div className="formio-builder-wrapper">
        <ConfigurationErrors errors={errors} />
        <MessageList messages={componentErrors} />
        <FormIOBuilder
          configuration={configuration}
          onChange={onChange}
          onComponentMutated={onComponentMutated.bind(null, url || generatedId)}
          {...props}
        />
      </div>
    </>
  );
};

FormStepDefinition.propTypes = {
  configuration: PropTypes.object,
  name: PropTypes.string,
  internalName: PropTypes.string,
  url: PropTypes.string,
  slug: PropTypes.string,
  previousText: PropTypes.string,
  saveText: PropTypes.string,
  nextText: PropTypes.string,
  loginRequired: PropTypes.bool,
  isReusable: PropTypes.bool,
  onChange: PropTypes.func.isRequired,
  onComponentMutated: PropTypes.func.isRequired,
  onFieldChange: PropTypes.func.isRequired,
  onLiteralFieldChange: PropTypes.func.isRequired,
  errors: PropTypes.arrayOf(PropTypes.arrayOf(PropTypes.string)),
};

const ConfigurationErrors = ({errors = []}) => {
  const configurationErrors = errors.filter(
    ([name, err]) => name === 'configuration' || name === 'formDefinition'
  );
  const [hasConfigurationErrors, formattedConfigurationErrors] =
    normalizeErrors(configurationErrors);
  if (!hasConfigurationErrors) return null;
  const errorMessages = formattedConfigurationErrors.map(msg => ({level: 'error', message: msg}));
  return <MessageList messages={errorMessages} />;
};

ConfigurationErrors.propTypes = {
  errors: PropTypes.arrayOf(PropTypes.arrayOf(PropTypes.string)),
};

const getComponentValidationErrors = (configuration, errors) => {
  const componentsWithErrors = errors
    .map(([path, message]) => {
      const [prefix, ...pathBits] = path.split('.');
      if (prefix !== 'configuration') return false;
      const field = pathBits.pop(); // last element = formio field name
      const component = get(configuration, pathBits);
      if (!component) return false;

      const intermediateComponents = [];
      for (let num = 1; num < pathBits.length - 1; num++) {
        const lookupPath = pathBits.slice(0, num);
        const intermediateComponent = get(configuration, lookupPath);
        if (!intermediateComponent.hasOwnProperty('label')) continue;
        intermediateComponents.push(intermediateComponent.label);
      }
      const componentLocation = intermediateComponents.join(' > ');
      return {
        componentLocation,
        component,
        field,
        message,
      };
    })
    .filter(Boolean);
  return componentsWithErrors;
};

export default FormStepDefinition;
