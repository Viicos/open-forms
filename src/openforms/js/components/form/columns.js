import {Formio} from 'formiojs';

import {LABEL, KEY, HIDDEN, CLEAR_ON_HIDE} from './edit/options';

const FormioColumnField = Formio.Components.components.columns;

const COLUM_EDIT_TABS = {
    key: 'display',
    label: 'Display',
    components: [
        LABEL,
        KEY,
        HIDDEN,
        CLEAR_ON_HIDE,
        {
            weight: 150,
            type: 'datagrid',
            input: true,
            key: 'columns',
            label: 'Column sizes',
            addAnother: 'Add Column',
            tooltip: 'Specify the size of each column. The sum of all the widths should be 100%.',
            reorder: false,
            defaultValue: [
                {size: '6', components: []},
                {size: '6', components: []},
            ],
            components: [
                {
                    type: 'hidden',
                    key: 'components',
                    defaultValue: []
                },
                {
                    type: 'select',
                    key: 'size',
                    label: 'Size',
                    defaultValue: '',
                    data: {
                        values: [
                            {label: '1/12 (8.33%)', value: '1'},
                            {label: '2/12 (16.67%)', value: '2'},
                            {label: '3/12 (25%)', value: '3'},
                            {label: '4/12 (33.33%)', value: '4'},
                            {label: '5/12 (41.67%)', value: '5'},
                            {label: '6/12 (50%)', value: '6'},
                            {label: '7/12 (58.33%)', value: '7'},
                            {label: '8/12 (66.67%)', value: '8'},
                            {label: '9/12 (75%)', value: '9'},
                            {label: '10/12 (83.33%)', value: '10'},
                            {label: '11/12 (91.67%)', value: '11'},
                        ],
                    },
                }
            ]
        }
    ]
};

class ColumnField extends FormioColumnField {
    static schema(...extend) {
        return FormioColumnField.schema({
            label: 'Columns',
            key: 'columns',
            type: 'columns',
            columns: [
                {size: '6', components: []},
                {size: '6', components: []},
            ],
        }, ...extend);
    }

    static get builderInfo() {
        return {
          title: 'Columns',
          icon: 'columns',
          group: 'layout',
          documentation: '/userguide/#columns',
          weight: 10,
          schema: ColumnField.schema()
        };
    }

    get defaultSchema() {
        return ColumnField.schema();
    }

    static editForm() {
        return {
            components: [
                {
                    type: 'tabs',
                    key: 'columns',
                    components: [COLUM_EDIT_TABS]
                },
            ]
        };
    }
}

export default ColumnField;
